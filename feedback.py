from flask import Flask, send_file
from flask_socketio import SocketIO
import RPi.GPIO as GPIO

app = Flask('feedback')
socketio = SocketIO(app)

GPIO.setmode(GPIO.BCM)
btn = 2
GPIO.setup(btn, GPIO.IN)

@app.route('/')
def index():
    return send_file('feedback.html')

@app.route('/images/<filename>')
def get_image(filename):
    print('images/'+filename)
    return send_file('images/'+filename)

@socketio.on('isPressed')
def checkButton(receivedData):
    if (GPIO.input(btn) == False):
        socketio.emit('button', 'pressed')
    else:
        socketio.emit('button', 'released')

socketio.run(app, debug=True, port=3000, host='0.0.0.0')