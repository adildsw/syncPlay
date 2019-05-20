from flask import Flask, request
import json

app = Flask(__name__)

state = "pause"
checksum = "null"
filename = "null"
time = "0"

@app.route('/')
def hello_world():
    return "Server for syncPlay\nDeveloped by AdilDSW"

@app.route('/syncplay', methods=['POST', 'GET'])
def syncplay():
    obj = [{"filename" : filename, "checksum" : checksum, "state" : state, "time" : time}]
    return json.dumps(obj)

@app.route('/syncplay/reset', methods=['POST', 'GET'])
def reset_syncplay():
    global state, checksum, filename, time, seek
    state = "stop"
    checksum = "null"
    filename = "null"
    time = "0"
    return "SUCCESS"

@app.route('/syncplay/load', methods=['POST', 'GET'])
def load_syncplay():
    global state, checksum, filename, time, seek
    filename = request.args.get("filename")
    checksum = request.args.get("checksum")
    state = request.args.get("state")
    time = request.args.get("time")

    return "SUCCESS"

@app.route('/syncplay/play', methods=['POST', 'GET'])
def play_syncplay():
    global state
    state = "play"
    return "SUCCESS"

@app.route('/syncplay/pause', methods=['POST', 'GET'])
def pause_syncplay():
    global state, time
    time = request.args.get("time")
    state = "pause"
    return "SUCCESS"

@app.route('/syncplay/stop', methods=['POST', 'GET'])
def stop_syncplay():
    global state, time
    time = 0
    state = "stop"
    return "SUCCESS"
