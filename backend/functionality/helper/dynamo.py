import boto3
from config import aws_access_key_id, aws_secret_access_key

import logging

dynamodb = boto3.resource('dynamodb', region_name="us-west-1", aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

database = dynamodb.Table('ca208')


def get_by_account(account):
    record = database.get_item(Key={'account': account})
    return record['Item']

def create_account(account, **kwargs):
    try:
        database.put_item(
            Item={
                    'account': account,
                    **kwargs
                }
            )
        return True
    except:
        return False

def update_by_account(account, **kwargs):
    try:
        expression = "SET "
        values = {}
        for k in kwargs:
            expression += '%s = :val_%s,' % (k,k)
            values[':val_%s' % k] = kwargs[k]
            logging.debug('Update %s for %s' % (k, account))
        expression = expression[:-1]
        database.update_item(
            Key={
                'account': account
            },
            UpdateExpression = expression,
            ExpressionAttributeValues=values
        )
        return True
    except:
        return False