import boto3
import json

from config import aws_access_key_id, aws_secret_access_key

import logging

sns = boto3.client('sns', region_name="us-west-1", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

def send_event_to_bucket(event_name, account, **kwargs):
    # Create a new message
    try:
        logging.debug("%s %s" % (event_name, account))
        sns.publish(TopicArn='arn:aws:sns:us-west-1:795682038600:pask-event', Message=json.dumps({'account': account, 'op': event_name, **kwargs}))
        return True
    except Exception as e:
        logging.exception("Some thing wrong.")
        return False

