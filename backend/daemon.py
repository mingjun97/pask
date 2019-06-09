from flask import Flask
from flask_socketio import SocketIO, emit, rooms
from config import secret
from random import randint
from threading import Thread
from uuid import uuid4
from time import sleep

db = dict()
sessions = dict()

app = Flask(__name__)
app.config['SECRET_KEY'] = secret

socketio = SocketIO(app)

@socketio.on('connect', namespace='/main')
def connect():
    print('connect')

@socketio.on('login', namespace='/main')
def login(data):
    try:
        if db[data['username']]['password'] == data['password']:
            sessions[rooms()[0]] = data['username']
    except:
        pass


@socketio.on('register', namespace='/main')
def register(data):
    if data['username'] in db:
        return
    else:
        db[data['username']] = {
            'password': data['password'],
            'cposition': [randint(0, 501), randint(0, 501)]
        }

@socketio.on('move', namespace='/main')
def move(data):
    try:
        Thread(target=move_handler, args=(sessions[rooms()[0]], data['target'])).start()
        emit('move')
    except:
        pass

def move_handler(account,target):
    this_thread = uuid4()
    db[account]['processor'] = this_thread
    position = db[account]['cposition']
    steps = [position[0] - target[0], position[1] - target[1]]
    length = (steps[0] ** 2 + steps[1] ** 2) ** 0.5
    length = 0.001 if length == 0 else length
    steps[0] = - steps[0] / length
    steps[1] = - steps[1] / length
    while (int(position[0]) != target[0] and int(position[1]) != target[1]) and db[account]['processor'] == this_thread:
        position[0] += steps[0]
        position[1] += steps[1]
        db[account]['cposition'] = [int(position[0]), int(position[1])]
        sleep(0.1)


@socketio.on('whoami', namespace='/main')
def whoami():
    try:
        uname = sessions[rooms()[0]]
        emit('whoami', {'username': uname, 'position': db[uname]['cposition']})
    except:
        pass

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')