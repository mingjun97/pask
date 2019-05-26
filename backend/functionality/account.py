from .helper import get_by_account, create_account, update_by_account
import logging

def login(account, password):
    account = get_by_account(account)
    try:
        if account['password'] == password:
            return True
    except:
        return False
    return False

def register(account, password):
    try:
        account = get_by_account(account)
        return False
    except:
        create_account(account, password=password)
        return True

def change_password(account, password, new_password):
    if login(account, password):
        if update_by_account(account, password = new_password):
            return True
        else:
            return False
    else:
        return False