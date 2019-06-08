from .helper import send_event_to_bucket, get_by_account

def send_move_operation(account, target):
    return send_event_to_bucket('move', account, target=target)

def get_position(account):
    return get_by_account(account)['position']