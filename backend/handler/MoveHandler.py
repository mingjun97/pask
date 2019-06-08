import boto3
import time
import json
import math
from threading import Thread

sqs = boto3.resource('sqs')
dynamodb = boto3.resource('dynamodb', region_name="us-west-1")
database = dynamodb.Table('ca208')

class Handler():
    def __init__(self, op, object, target, left_time):
        self.queue_name = 'tmp_%s_%s.fifo' %(op, object)
        self.left = left_time
        self.object = object
        self.op = op
        self.processing = True
        self.target = target
        self.finished = False
        try:
            self.queue = sqs.get_queue_by_name(QueueName='fallback_' + self.queue_name)
            # TODO queue not exsit
            self.queue = sqs.create_queue(QueueName=queue_name, Attributes={'FifoQueue': 'true', 'identifier': str(time.time())})
            if op == 'move':
                t = Thread(target = self.processor_move)
            elif op == 'push':
                t = Thread(target = self.processor_push)
            t.start()
            while self.processing:
                try:
                    message = self.queue.receive_messages()[0]
                    self.target = json.loads(message)
                except:
                    pass
            self.queue.delete()
            if not finished:
                sns = boto3.client('sns')
                sns.publish(TopicArn='arn:aws:sns:us-west-1:795682038600:pask-event', Message=json.dumps({'account': self.object, 'op': self.op, 'target': self.target}))
        except EOFError: # Queue has already exsited
            queue = sqs.get_queue_by_name(QueueName=self.queue_name)
            queue.purge()
            queue.send_message(MessageBody=json.dumps(target), MessageGroupId="move")
            return
        except : # Queue has been deleted within 60 secondes
            try:
                self.queue = sqs.create_queue(QueueName='fallback_' + self.queue_name, Attributes={'FifoQueue': 'true', 'identifier': str(time.time())})

                # TODO: Attach to fallback queue and do processing
            except: # Fall back queue has already exsited.
                self.queue = sqs.get_queue_by_name(QueueName='fallback_' + self.queue_name)
                self.queue.send_message() # forward request to fallback queue.

    
    def processor_move(self):
        try:
            record = database.get_item(Key={'account': self.object})['Item']
        except:
            self.processing = False
            return
        try:
            position = record['positon']
            position[0] = float(position[0])
            position[1] = float(position[1])
        except:
            position = [250.0, 250.0]
        target = None
        steps = [0, 0]
        while self.processing:
            if target != self.target:
                target = self.target
                alpha = math.atan((position[1] - target[1])/(position[0] - target[0]))
                steps = [math.cos(alpha) * abs(target[0]-position[0])/(target[0]-position[0]),
                         math.sin(alpha) * abs(target[1]-position[1])/(target[1]-position[1])]
            if self.left() < 1000: # Quit to avoid lambda timeout
                self.processing = False
            else:
                position[0] += steps[0]
                position[1] += steps[1]
                self.update('position', [int(position[0]), int(position[1])])
                time.sleep(0.1)

    def update(self, key, data):
        Thread(target=database.update_item, kwargs={
            "Key": {'account': self.object},
            "UpdateExpression": 'SET %s=:val_1' % key,
            "ExpressionAttributeValues": {':val_1': data}
        }).start()
        return

    def processor_push(self):
        pass
