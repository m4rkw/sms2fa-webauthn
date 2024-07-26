import os
import sys
import boto3
from webauthn import generate_registration_options, options_to_json, verify_registration_response, base64url_to_bytes, generate_authentication_options, verify_authentication_response
from base64 import urlsafe_b64decode, urlsafe_b64encode
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
import datetime
import uuid

class SMS2FA_Authenticate:

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
                "Access-Control-Allow-Methods": "'POST,OPTIONS'"
            }
        }


    def main(self, event):
        if event['queryStringParameters'] is None:
            self.audit(event, 'authentication-failed', f"missing query string")
            return self.response(400)

        if 'session_id' not in event['queryStringParameters']:
            self.audit(event, 'authentication-failed', f"missing session_id")
            return self.response(400)

        if not re.match(r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b', event['queryStringParameters']['session_id']):
            self.audit(event, 'authentication-failed', f"invalid session_id")
            return self.response(400)

        if 'body' not in event:
            self.audit(event, 'authentication-failed', f"missing body")
            return self.response(400)

        try:
            body = json.loads(event['body'])
        except Exception as e:
            self.audit(event, 'authentication-failed', f"failed to parse JSON payload: {str(e)}")
            self.log(event['body'])
            return self.response(400)

        if 'authentication_data' not in body:
            self.audit(event, 'authentication-failed', f"authentication_data not found in JSON payload")
            return self.response(400)

        authentication_data = body['authentication_data']

        resp = self.dbd.get_item(
            TableName='sms2fa_user',
            Key={
                'user_id': {'S': body['user_id']}
            }
        )

        if 'Item' not in resp:
            self.audit(event, 'authentication-failed', f"user not found: {body['user_id']}")

            return self.response(400, 'user not found')

        user_id = resp['Item']['user_id']['S']
        user = pickle.loads(base64.b64decode(resp['Item']['credential']['S'].encode('utf8')))

        resp = self.dbd.get_item(
            TableName='sms2fa_authoptions',
            Key={
                'session_id': {'S': event['queryStringParameters']['session_id']}
            }
        )

        if 'Item' not in resp:
            self.audit(event, 'authentication-failed', f"session not found: {event['queryStringParameters']['session_id']}")

            return self.response(400, 'session not found')

        if resp['Item']['useragent']['S'] != event['requestContext']['identity']['userAgent']:
            self.audit(event, 'authentication-failed', f"user agent mismatch, {event['requestContext']['identity']['userAgent']} != {resp['Item']['useragent']['S']}")

            return self.response(400, 'session not found')

        if resp['Item']['ipaddr']['S'] != event['requestContext']['identity']['sourceIp']:
            self.audit(event, 'authentication-failed', f"source IP mismatch, {event['requestContext']['identity']['sourceIp']} != {resp['Item']['ipaddr']['S']}")

            return self.response(400, 'session not found')

        timestamp = float(resp['Item']['timestamp']['S'])

        if time.time() - timestamp >= 300:
            self.dbd.delete_item(
                TableName='sms2fa_authoptions',
                Key={
                    'session_id': {'S': event['queryStringParameters']['session_id']}
                }
            )

            self.audit(event, 'authentication-failed', f"session expired: {event['queryStringParameters']['session_id']}")

            return self.response(400, 'session expired')

        challenge = pickle.loads(base64.b64decode(resp['Item']['authoptions']['S'].encode('utf8')))

        credential_id = user['credential_id']
        public_key = user['public_key']

        response = AuthenticatorAssertionResponse(
            authenticator_data=urlsafe_b64decode(authentication_data['response']['authenticatorData']),
            client_data_json=urlsafe_b64decode(authentication_data['response']['clientDataJSON']),
            signature=urlsafe_b64decode(authentication_data['response']['signature'])
        )

        try:
            credential = AuthenticationCredential(
                id=credential_id,
                raw_id=urlsafe_b64decode(authentication_data['rawId']),
                response=response,
                type='public-key'
            )

            verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_origin=f'https://{self.auth_endpoint}',
                expected_rp_id=self.auth_endpoint,
                credential_public_key=public_key,
                credential_current_sign_count=user['sign_count']  # Retrieve and increment stored sign count
            )

            self.dbd.delete_item(
                TableName='sms2fa_authoptions',
                Key={
                    'session_id': {'S': event['queryStringParameters']['session_id']}
                }
            )

            resp = self.dbd.get_item(
                TableName='sms2fa',
                Key={
                    'token': {'S': body['token']}
                }
            )

            self.dbd.delete_item(
                TableName='sms2fa',
                Key={
                    'token': {'S': body['token']}
                }
            )

            if 'Item' in resp:
                self.audit(event, 'authentication-success')

                return self.response(200, {'code': resp['Item']['code']['S']})
            else:
                self.audit(event, 'authentication-failed', f"invalid token: {body['token']}")

                return self.response(400, 'invalid token')

        except WebAuthnException as e:
            self.log(f"webauthn exception: {str(e)}")

            self.audit(event, 'authentication-failed', f"exception: {str(e)}")

            return self.response(500, "internal server error")


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
    s = SMS2FA_Authenticate()
    return(s.main(event))
