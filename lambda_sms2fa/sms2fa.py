import os
import sys
import boto3
import json
import re
from pushover import Client
import urllib.parse
import time
import uuid
import datetime

class SMS2FA:

    def __init__(self):
        self.log('initialising dynamodb client')

        self.dbd = boto3.client('dynamodb')

        self.log('initialising pushover client')

        self.pushover = Client(os.environ['PUSHOVER_USER'], api_token=os.environ['PUSHOVER_APP'])
        self.auth_endpoint = os.environ['AUTH_ENDPOINT']
        self.provider_regex = os.environ['PROVIDER_REGEX']
        self.provider_from_segment = int(os.environ['PROVIDER_FROM_SEGMENT'])
        self.provider_message_segment = int(os.environ['PROVIDER_MESSAGE_SEGMENT'])


    def response(self, status_code, message='invalid request'):
        if status_code == 200:
            resp = {'status': 'ok'}
        else:
            resp = {'status': 'error', 'error': message}

        return {
            "isBase64Encoded": False,
            "statusCode": status_code,
            "body": json.dumps(resp),
            "headers": {
                "Content-Type": "application/json"
            }
        }


    def main(self, event):
        try:
            regex = re.compile(self.provider_regex)
        except Exception as e:
            self.audit(event, 'regex-error', f"failed to compile regex '{self.provider_regex}': {str(e)}")
            return self.response(500, 'internal server error')

        if 'body' not in event:
            self.audit(event, 'missing-body', f"missing body")
            return self.response(400)

        m = re.match(regex, event['body'])

        if not m:
            self.audit(event, 'regex-error', f"failed to parse payload with provider regex")
            self.log(f"regex: {self.provider_regex}")
            self.log(f"payload: {event['body']}")
            return self.response(400)

        _from = m.group(self.provider_from_segment)
        message = urllib.parse.unquote(m.group(self.provider_message_segment)).replace('+',' ')

        if _from[0:2] == '44':
            _from = '0' + _from[self.provider_from_segment:]

        content = message

        # strip out telephone numbers so we don't incorrectly match them as OTP codes
        match_content = content

        for telno in re.findall(r'[\d]{4} [\d]{3} [\d]{4}', content):
            match_content = content.replace(telno, '')

        code = None

        m = re.match(r'^.*?(G-[\d]{6})', match_content)

        if m:
            # google format OTP codes
            code = m.group(1)
        else:
            # generically look for OTP codes as 8/6/4-digits
            codes = re.findall(r'[\d]+', match_content)

            for potential_code in codes:
                if len(potential_code) in [8,6,4]:
                    code = potential_code
                    break

        if code is None:
            self.audit(event, 'sms-received', message, _from)
            self.pushover.send_message(message, title=_from)
        else:
            token = str(uuid.uuid4())
            self.audit(event, 'sms-received', message.replace(code, ('X' * (len(code)))), _from, token)

            self.dbd.put_item(
                TableName='sms2fa',
                Item={
                    'token': {'S': token},
                    'timestamp': {'S': str(time.time())},
                    'code': {'S': code}
                }
            )

            url = f'https://{self.auth_endpoint}/?token={token}'

            self.pushover.send_message('OTP', title=_from, url=url)

        return self.response(200)


    def log(self, message):
        sys.stderr.write(message + "\n")
        sys.stderr.flush()


    def audit(self, event, event_type, message, from_number=None, token=None):
        log_message = f"{event_type} - {event['requestContext']['identity']['sourceIp']} - {event['requestContext']['path']} [{event['requestContext']['identity']['userAgent']}]"

        if from_number is not None:
            log_message += f" - {from_number}"

        log_message += f" - {message}"

        self.log(log_message)

        audit_id = str(uuid.uuid4())
        timestamp = str(int(time.time()))

        obj = {
            'id': {'S': audit_id},
            'event': {'S': event_type},
            'resource': {'S': event['requestContext']['path']},
            'timestamp': {'N': timestamp},
            'ipaddr': {'S': event['requestContext']['identity']['sourceIp']},
            'useragent': {'S': event['requestContext']['identity']['userAgent']},
            'message': {'S': message}
        }

        if from_number is not None:
            obj['from'] = {'S': from_number}

        if token is not None:
            obj['token'] = {'S': token}

        self.dbd.put_item(
            TableName="sms2fa_audit",
            Item=obj
        )


def handler(event, context):
    s = SMS2FA()
    return(s.main(event))
