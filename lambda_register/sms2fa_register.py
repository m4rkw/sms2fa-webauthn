import os
import sys
import boto3
from webauthn import generate_registration_options, options_to_json, verify_registration_response, base64url_to_bytes
from webauthn.helpers.structs import (
    PublicKeyCredentialCreationOptions,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment,
    RegistrationCredential,
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    AuthenticatorAttestationResponse,
)
from base64 import urlsafe_b64decode
from pushover import Client
import base64
import pickle
import json
import time
import uuid

class SMS2FA_Register:

    def __init__(self):
        self.log('initialising dynamodb client')

        self.dbd = boto3.client('dynamodb')
        self.pushover = Client(os.environ['PUSHOVER_USER'], api_token=os.environ['PUSHOVER_APP'])

        self.auth_endpoint = os.environ['AUTH_ENDPOINT']
        self.session_id = None


    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()


    def response(self, status_code, message='invalid request'):
        if status_code == 200:
            if type(message) == dict:
                resp = message
            else:
                resp = {}

            resp['status'] = 'ok'
        else:
            resp = {'status': 'error', 'error': message}

        return {
            "isBase64Encoded": False,
            "statusCode": status_code,
            "body": json.dumps(resp),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": f"https://{self.auth_endpoint}",
                "Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                "Access-Control-Allow-Methods": "'POST,OPTIONS'"
            }
        }


    def main(self, event):
        if 'body' not in event:
            self.audit(event, 'registration-failed', 'missing body')
            return self.response(400)

        try:
            data = json.loads(event['body'])
        except Exception as e:
            self.audit(event, 'registration-failed', f"failed to parse JSON body: {str(e)}")
            self.log(event['body'])
            return self.response(400)

        if 'sessionId' not in data:
            self.audit(event, 'registration-failed', f"missing sessionId")
            self.log(event['body'])
            return self.response(400)

        self.session_id = data['sessionId']

        resp = self.dbd.get_item(
            TableName='sms2fa_regoptions',
            Key={
                'session_id': {'S': self.session_id}
            }
        )

        if 'Item' not in resp:
            self.audit(event, 'registration-failed', f"invalid session_id: {self.session_id}")
            return self.response(400, 'invalid session_id')

        if resp['Item']['useragent']['S'] != event['requestContext']['identity']['userAgent']:
            self.audit(event, 'registration-failed', f"user agent mismatch, {event['requestContext']['identity']['userAgent']} != {resp['Item']['useragent']['S']}")

            return self.response(400, 'session not found')

        if resp['Item']['ipaddr']['S'] != event['requestContext']['identity']['sourceIp']:
            self.audit(event, 'registration-failed', f"source IP mismatch, {event['requestContext']['identity']['sourceIp']} != {resp['Item']['ipaddr']['S']}")

            return self.response(400, 'session not found')

        session = json.loads(resp['Item']['regoptions']['S'])

        timestamp = float(resp['Item']['timestamp']['S'])

        if time.time() - timestamp >= 300:
            self.dbd.delete_item(
                TableName='sms2fa_regoptions',
                Key={
                    'session_id': {'S': self.session_id}
                }
            )

            self.audit(event, 'registration-failed', f"session expired")

            return self.response(400, 'session expired')

        resp = self.dbd.get_item(
            TableName='sms2fa_regtoken',
            Key={
                'token': {'S': data['token']}
            }
        )

        if 'Item' not in resp:
            self.audit(event, 'registration-failed', f"invalid registration token")

            return self.response(400, 'invalid registration token')

        timestamp = float(resp['Item']['timestamp']['S'])

        if time.time() - timestamp >= 300:
            self.dbd.delete_item(
                TableName='sms2fa_regtoken',
                Key={
                    'token': {'S': data['token']}
                }
            )

            self.audit(event, 'registration-failed', f"registration token expired")

            return self.response(400, 'registration token expired')

        response = AuthenticatorAttestationResponse(
            attestation_object=urlsafe_b64decode(data['response']['attestationObject']),
            client_data_json=urlsafe_b64decode(data['response']['clientDataJSON'])
        )

        credential = RegistrationCredential(
            id=data['id'],
            raw_id=urlsafe_b64decode(data['rawId']),
            response=response,
            type=data['type']
        )

        try:
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=session['challenge'].encode('utf8'),
                expected_origin=f'https://{self.auth_endpoint}',
                expected_rp_id=self.auth_endpoint
            )

            self.dbd.delete_item(
                TableName='sms2fa_regtoken',
                Key={
                    'token': {'S': data['token']}
                }
            )

            resp = self.dbd.get_item(
                TableName='sms2fa_user',
                Key={
                    'user_id': {'S': 'user_id'}
                }
            )

            resp = self.dbd.scan(
                TableName='sms2fa_user'
            )

            if 'Items' in resp:
                for item in resp['Items']:
                    self.dbd.delete_item(
                        TableName='sms2fa_user',
                        Key={
                            'user_id': {'S': item['user_id']['S']}
                        }
                    )

            self.dbd.put_item(
                TableName='sms2fa_user',
                Item={
                    'user_id': {'S': credential.id},
                    'user_name': {'S': 'sms2fa'},
                    'credential': {'S': base64.b64encode(pickle.dumps({
                        'credential_id': credential.id,
                        'public_key': verification.credential_public_key,
                        'sign_count': verification.sign_count
                    })).decode('utf8')}
                }
            )

            self.dbd.put_item(
                TableName='sms2fa_user',
                Item={
                    'user_id': {'S': 'user_id'},
                    'credential_id': {'S': credential.id}
                }
            )

            self.audit(event, 'registration-success')

            self.pushover.send_message('Passkey registered', title='SMS2FA')

            return self.response(200)
        except Exception as e:
            self.log(f"caught exception: {str(e)}")

            self.audit(event, 'registration-failed', f"exception: {str(e)}")

            return self.response(500, 'internal server error')


    def audit(self, event, event_type, message=None):
        log_message = f"{event_type} - {event['requestContext']['identity']['sourceIp']} - {event['requestContext']['path']} [{event['requestContext']['identity']['userAgent']}]"

        if message is not None:
            log_message += f" - {message}"

        self.log(log_message)

        audit_id = str(uuid.uuid4())
        timestamp = str(int(time.time()))

        if message is None:
            message = ''

        obj = {
            'id': {'S': audit_id},
            'event': {'S': event_type},
            'resource': {'S': event['requestContext']['path']},
            'timestamp': {'N': timestamp},
            'ipaddr': {'S': event['requestContext']['identity']['sourceIp']},
            'useragent': {'S': event['requestContext']['identity']['userAgent']},
            'message': {'S': message}
        }

        if self.session_id is not None:
            obj['session_id'] = {'S': self.session_id}

        self.dbd.put_item(
            TableName="sms2fa_audit",
            Item=obj
        )


def handler(event, context):
    s = SMS2FA_Register()
    return(s.main(event))
