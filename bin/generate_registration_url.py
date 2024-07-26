#!/usr/bin/env python3

import boto3
import uuid
import time
import os

auth_endpoint = os.popen("cat terraform.tfvars |grep auth_endpoint |xargs").read().rstrip().split(" ")[2]

dbd = boto3.client('dynamodb')

token = str(uuid.uuid4())

user = 'sms2fa'

dbd.put_item(
    TableName='sms2fa_regtoken',
    Item={
        'user_id': {'S': user},
        'token': {'S': token},
        'timestamp': {'S': str(time.time())}
    }
)

print(f"https://{auth_endpoint}/register.html?user_id={user}&token={token}")
