import base64
import gzip
import json
import os
from botocore.exceptions import ClientError
import boto3
import logging
from datetime import datetime

def lambda_handler(event, context):
    cw_data = event['awslogs']['data']
    compressed_payload = base64.b64decode(cw_data)
    uncompressed_payload = gzip.decompress(compressed_payload)
    data = json.loads(uncompressed_payload.decode('utf-8'))
    sqs_url = os.environ.get("SqsMeteringUsersUrl")
    customerID = os.environ.get("customerID")
    users = 0
    sqs = boto3.client('sqs')

    for event in data['logEvents']:
        message = json.loads(event['message'])
        source = message['eventSource']
        event = message['eventName']
        
        if event == 'DeleteUser':
            users = -1
        elif event == 'CreateUser':
            users = 1
        
        msm_body = { 
            "Type": "Notification", 
            "Message" : {
                "action" : "users-updated",
                "customer_id": customerID,
                "user_numbers": users,
                "time": datetime.now().isoformat(" ")
            } 
        }
        try:
            sqs.send_message(QueueUrl = sqs_url, MessageBody = json.dumps(msm_body),MessageGroupId = source)
        
        except ClientError as e:
            logging.exception(f"Unexpected error: {e}")
            return
   
        
        
    return {
        'statusCode': 200,
        'body': json.dumps('users are metered')
    }
