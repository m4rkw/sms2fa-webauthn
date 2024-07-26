#!/usr/bin/env python3

import boto3
import uuid
import time
import os
import sys
import shutil
import tabulate
import datetime

def read_all_sorted_records(table_name, range_key):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    response = table.scan()
    items = response.get('Items', [])

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    sorted_items = sorted(items, key=lambda x: x[range_key])
    return sorted_items

def wrap_text(text, max_length):
    words = text.split()
    wrapped_text = []
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > max_length:
            wrapped_text.append(line)
            line = word
        else:
            if line:
                line += " "
            line += word
    wrapped_text.append(line)
    return "\n".join(wrapped_text)

records = read_all_sorted_records('sms2fa_audit', 'timestamp')

fields = ["timestamp","event","ipaddr","resource","from","message"]

data = []

width, _ = shutil.get_terminal_size(fallback=(80, 20))

for record in records:
    record['timestamp'] = datetime.datetime.fromtimestamp(int(record['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')

    row = []

    for key in fields:
        if key not in record:
            record[key] = ''

        if key == 'message':
            record[key] = wrap_text(record[key], width - 100)

        row.append(record[key])

    data.append(row)

print(tabulate.tabulate([fields] + data, headers='firstrow'))
