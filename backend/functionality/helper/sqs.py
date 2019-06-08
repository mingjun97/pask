import boto3
import json

from config import aws_access_key_id, aws_secret_access_key

sqs = boto3.resource('sqs', region_name="us-west-1", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

def send_event_to_bucket(event_name, account, **kwargs):
    queue = sqs.get_queue_by_name(QueueName='event-bucket')
    # Create a new message
    try:
        queue.send_message(MessageBody=json.dumps({'account': account, 'op': event_name, **kwargs}))
        return True
    except:
        return False

