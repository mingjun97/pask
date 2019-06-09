import boto3
import time
import json
import math
from threading import Thread

sqs = boto3.resource('sqs')
dynamodb = boto3.resource('dynamodb', region_name="us-west-1")
database = dynamodb.Table('cs208')

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
            self.groupId = float(database.get_item(Key={'account': self.object})['Item']['operation_groupId'][op])
        except:
            self.groupId = 0
        try:
            self.queue = sqs.get_queue_by_name(QueueName=self.queue_name)
            # Primary queue exsited
        # Primary queue doesn't exsit
        except: 
            self.queue = sqs.create_queue(QueueName=self.queue_name, Attributes={'FifoQueue': 'true'})
        if self.groupId + 890 < time.time():
            self.groupId = time.time()
            self.updateGroupId(groupId=self.groupId)
            Thread(target=self.processor_move).start()
            while self.processing:
                time.sleep(0.05)
                messages = self.queue.receive_messages(AttributeNames=['MessageGroupId'])
                if len(messages) == 0:
                    continue
                if float(messages[0].attributes['MessageGroupId']) > self.groupId:
                    self.processing = False
                    messages[0].change_visibility(VisibilityTimeout=0)
                elif float(messages[0].attributes['MessageGroupId']) == self.groupId:
                    self.target = json.loads(messages[0].body)
                    messages[0].delete()
        else:
            self.queue.send_message(MessageBody=json.dumps(target), MessageGroupId=str(self.groupId), MessageDeduplicationId=str(time.time()))
    
    def processor_move(self):
        try:
            record = database.get_item(Key={'account': self.object})['Item']
        except:
            self.processing = False
            return
        try:
            position = record['cposition']
            position[0] = float(position[0])
            position[1] = float(position[1])
        except:
            position = [250.0, 250.0]
        target = None
        while self.processing:
            if target != self.target:
                target = self.target
                steps = [position[0] - target[0], position[1] - target[1]]
                length = (steps[0] ** 2 + steps[1] ** 2) ** 0.5
                length = 0.001 if length == 0 else length
                steps[0] = - steps[0] / length
                steps[1] = - steps[1] / length
            if self.left() < 1000: # Quit in advance to avoid lambda timeout
                self.processing = False
                self.updateGroupId()
            else:
                position[0] += steps[0]
                position[1] += steps[1]
                if int(position[0]) == target[0] and int(position[1]) == target[1]:
                    self.processing = False
                    self.updateGroupId()
                self.update('cposition', [int(position[0]), int(position[1])])
                time.sleep(0.1)

    def update(self, key, data):
        # print(data)
        if (key != 'operation_groupId'):
            try:
                if database.get_item(Key={'account': self.object})['Item']['operation_groupId'][op] == self.groupId:
                    Thread(target=database.update_item, kwargs={
                        "Key": {'account': self.object},
                        "UpdateExpression": 'SET %s=:val_1' % key,
                        "ExpressionAttributeValues": {':val_1': data}
                    }).start()
                else:
                    self.processing = False
            except:
                Thread(target=database.update_item, kwargs={
                        "Key": {'account': self.object},
                        "UpdateExpression": 'SET %s=:val_1' % key,
                        "ExpressionAttributeValues": {':val_1': data}
                }).start()
        else:
            Thread(target=database.update_item, kwargs={
                "Key": {'account': self.object},
                "UpdateExpression": 'SET %s=:val_1' % key,
                "ExpressionAttributeValues": {':val_1': data}
            }).start()
        return

    def updateGroupId(self, groupId=0):
        self.update('operation_groupId', {self.op: str(groupId)})

    def processor_push(self):
        pass
