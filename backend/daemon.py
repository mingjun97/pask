from flask import Flask
from flask_socketio import SocketIO, emit, rooms
from config import secret
from random import randint

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
    print(data)

@socketio.on('whoami', namespace='/main')
def whoami():
    try:
        uname = sessions[rooms()[0]]
        emit('whoami', {'username': uname, 'position': db[uname]['cposition']})
    except:
        pass

if __name__ == "__main__":
    socketio.run(app)