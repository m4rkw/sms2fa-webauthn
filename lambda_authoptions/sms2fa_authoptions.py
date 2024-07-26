import os
import sys
import boto3
from webauthn import generate_registration_options, options_to_json, verify_registration_response, base64url_to_bytes, generate_authentication_options
from webauthn.helpers.structs import (
    AuthenticationCredential,
    PublicKeyCredentialRequestOptions,
    PublicKeyCredentialRpEntity,
    AuthenticatorSelectionCriteria,
    AuthenticatorAttachment,
    UserVerificationRequirement,
    AuthenticatorAssertionResponse,
)
from webauthn.helpers.exceptions import WebAuthnException
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import base64
import pickle
import json
import time
import re
import uuid

class SMS2FA_AuthOptions:

    def __init__(self):
        self.log('initialising dynamodb client')

        self.dbd = boto3.client('dynamodb')

        self.auth_endpoint = os.environ['AUTH_ENDPOINT']

        self.rp_entity = PublicKeyCredentialRpEntity(
            id=self.auth_endpoint,
            name=self.auth_endpoint
        )


    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()


    def response(self, status_code, message='invalid request'):
        if status_code == 200:
            resp = message
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
                "Access-Control-Allow-Methods": "'GET,OPTIONS'"
            }
        }


    def main(self, event):
        if event['queryStringParameters'] is None:
            self.audit(event, 'authoptions-failed', 'missing query string')

            return self.response(400)

        if 'session_id' not in event['queryStringParameters']:
            self.audit(event, 'authoptions-failed', 'missing session_id')

            return self.response(400)

        if not re.match(r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b', event['queryStringParameters']['session_id']):
            self.audit(event, 'authoptions-failed', 'invalid session_id')

            return self.response(400)

        resp = self.dbd.get_item(
            TableName='sms2fa_user',
            Key={'user_id': {'S': 'user_id'}}
        )

        if 'Item' not in resp:
            self.audit(event, 'authoptions-failed', 'user not found')

            return self.response(400, 'user not found')

        resp = self.dbd.get_item(
            TableName='sms2fa_user',
            Key={'user_id': {'S': resp['Item']['credential_id']['S']}}
        )

        if 'Item' not in resp:
            self.audit(event, 'authoptions-failed', 'user not found')

            return self.response(400, 'user not found')

        user_id = resp['Item']['user_id']['S']
        user = pickle.loads(base64.b64decode(resp['Item']['credential']['S'].encode('utf8')))

        credential_id = user['credential_id']
        public_key = user['public_key']

        authenticator_selection = AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.PREFERRED,
            require_resident_key=True,
        )

        options = generate_authentication_options(
            rp_id=self.rp_entity.id,
            user_verification=UserVerificationRequirement.PREFERRED,
        )

        int_array = [int(byte) for byte in options.challenge]

        resp = self.dbd.get_item(
            TableName='sms2fa_authoptions',
            Key={
                'session_id': {'S': event['queryStringParameters']['session_id']}
            }
        )

        if 'Item' in resp:
            self.dbd.delete_item(
                TableName='sms2fa_authoptions',
                Key={
                    'session_id': {'S': event['queryStringParameters']['session_id']}
                }
            )

        self.dbd.put_item(
            TableName='sms2fa_authoptions',
            Item={
                'user_id': {'S': user_id},
                'session_id': {'S': event['queryStringParameters']['session_id']},
                'authoptions': {'S': base64.b64encode(pickle.dumps(options.challenge)).decode('utf8')},
                'timestamp': {'S': str(time.time())},
                'useragent': {'S': event['requestContext']['identity']['userAgent']},
                'ipaddr': {'S': event['requestContext']['identity']['sourceIp']}
            }
        )

        resp = {
            'authoptions': {
                'challenge': int_array,
                'allow_credentials': [{
                    'type': cred['type'],
                    'id': urlsafe_b64encode(cred['id']).decode('utf-8'),
                    'transports': cred.get('transports', [])
                } for cred in options.allow_credentials]
            }
        }

        self.audit(event, 'authoptions-success')

        return self.response(200, resp)


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

        if event['queryStringParameters'] is not None and 'session_id' in event['queryStringParameters']:
            obj['session_id'] = {'S': event['queryStringParameters']['session_id']}

        self.dbd.put_item(
            TableName="sms2fa_audit",
            Item=obj
        )


def handler(event, context):
    s = SMS2FA_AuthOptions()
    return(s.main(event))
