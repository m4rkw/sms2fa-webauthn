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
)
import os
import base64
import pickle
import json
import time
import re
import uuid

class SMS2FA_RegOptions:

    def __init__(self):
        self.log('initialising dynamodb client')

        self.dbd = boto3.client('dynamodb')

        self.auth_endpoint = os.environ['AUTH_ENDPOINT']


    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()


    def response(self, status_code, message='invalid request'):
        if status_code == 200:
            resp = message
        else:
            resp = json.dumps({'status': 'error', 'error': message})

        return {
            "isBase64Encoded": False,
            "statusCode": status_code,
            "body": resp,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": f"https://{self.auth_endpoint}",
                "Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                "Access-Control-Allow-Methods": "'GET,OPTIONS'"
            }
        }


    def main(self, event):
        if event['queryStringParameters'] is None:
            self.audit(event, 'regoptions-failed', 'missing query string')
            return self.response(400)

        for key in ['session_id','user_id','token']:
            if key not in event['queryStringParameters']:
                self.audit(event, 'regoptions-failed', f'missing {key}')
                return self.response(400)

        for key in ['session_id','token']:
            if not re.match(r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b', event['queryStringParameters'][key]):
                self.audit(event, 'regoptions-failed', f'invalid {key}')
                return self.response(400)

        session_id = event['queryStringParameters']['session_id']
        user_id = event['queryStringParameters']['user_id']
        token = event['queryStringParameters']['token']

        resp = self.dbd.get_item(
            TableName='sms2fa_regtoken',
            Key={
                'token': {'S': token}
            }
        )

        if 'Item' not in resp:
            self.audit(event, 'regoptions-failed', f'invalid registration token: {token}')
            return self.response(400, "invalid registration token")

        user_id = 'sms2fa'  # Replace with your actual user ID
        user_name = 'sms2fa'  # Replace with your actual user name

        user_entity = PublicKeyCredentialUserEntity(
            id=user_id.encode('utf-8'),
            name=user_name,
            display_name='sms2fa'
        )

        authenticator_selection = AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=UserVerificationRequirement.REQUIRED,
        )

        registration_options = generate_registration_options(
            rp_id=self.auth_endpoint,
            rp_name=self.auth_endpoint,
            user_name="sms2fa",
            authenticator_selection=authenticator_selection
        )

        regoptions_json = options_to_json(registration_options)
        regoptions = json.loads(regoptions_json)
        regoptions = json.dumps({
            'status': 'ok',
            'regoptions': regoptions
        })

        self.dbd.put_item(
            TableName='sms2fa_regoptions',
            Item={
                'user_id': {'S': 'sms2fa'},
                'session_id': {'S': session_id},
                'timestamp': {'S': str(time.time())},
                'regoptions': {'S': regoptions_json},
                'useragent': {'S': event['requestContext']['identity']['userAgent']},
                'ipaddr': {'S': event['requestContext']['identity']['sourceIp']}
            }
        )

        self.audit(event, 'regoptions-success')

        return self.response(200, regoptions)


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
    s = SMS2FA_RegOptions()
    return(s.main(event))
