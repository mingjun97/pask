# This file is for lambda function.

import json
import hashlib
from time import time
from config import secret
from base64 import b64encode
from functionality.account import login, register, change_password
import logging

def generate_return(code, **kwargs):
    if code == 200:
        return {
            "code": 200,
            "message": "Success",
            **kwargs
        }
    if code == 403:
        return {
            "code": 403,
            "message": "Something wrong."
        }
    if code == 401:
        return {
            "code": 401,
            "message": "Please do authentication first."
        }
    if code == 404:
        return {
            "code": 404,
            "message": "Not Found"
        }

def vilidate(token):
    # Token should looks like: ACCOUNT:VALID_UNTIL:SIGNITURE
    try:
        m = hashlib.sha256()
        token = token.split(':')
        if time() > float(token[1]):
            logging.debug("Timestamp check failed!")
            return False
        m.update(token[0].encode('utf-8'))
        m.update(token[1].encode('utf-8'))
        m.update(secret.encode('utf-8')) 
        logging.debug(b64encode(m.digest()).decode('utf-8') + "  " + token[2])
        if b64encode(m.digest()).decode('utf-8') != token[2]:
            logging.debug("Signiture check failed!")
            return False
        return True
    except:
        return False

def generate_token(account):
    logging.debug("Generate token for %s" % account)
    m = hashlib.sha256()
    timestamp = time() + 60 * 10
    m.update(account.encode('utf-8'))
    m.update(str(timestamp).encode('utf-8'))
    m.update(secret.encode('utf-8'))
    return "%s:%s:%s" % (account, str(timestamp), b64encode(m.digest()).decode('utf-8'))

def check_login(event):
    if login(event['account'], event['password']):
        return generate_return(200 ,token=generate_token(event['account']))
    else:
        return generate_return(403)

def try_register(event):
    try:
        if register(event['account'], event['password']):
            return generate_return(200)
    except:
        return generate_return(403) 

def new_password(event):
    try:
        if change_password(event['account'], event['password'], event['new_password']):
            return generate_return(200)
        else:
            return generate_return(401)
    except:
        return generate_return(403)

def handler(event, context):
    try:
        if event['op'] == 'login':
            return check_login(event)
        if event['op'] == 'register':
            return try_register(event)
        if event['op'] == 'new_password':
            return new_password(event)

        if ('token' not in event or not vilidate(event['token'])):
            return generate_return(401)
    except:
        pass
    return generate_return(404)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(handler({"token": "test1:1558908258.354367:wpFt5sDPiNkLgHde8FrAmW2IeINEsaUx0YIc+fhNygI=", 'op': ''}, ""))
    # print(handler({"token": "test:1558903983.5422819:GLJuIJvV8fdnPUpoFEXu9sotdp2Rt5PC/CO/+tJWBIQ=", 'op': 'login', 'account': 'test', 'password': 'test'}, ""))
    # print(handler({'op': 'new_password', 'account': 'test1', 'password': 'bar', 'new_password': 'for'}, ""))
    # print(handler({'op': 'login', 'account': 'test1', 'password': 'for'}, ""))

    # print(generate_token('test'))