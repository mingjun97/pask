from .helper import send_event_to_bucket

def send_move_operation(account, target):
    return send_event_to_bucket('move', account, target=target)
