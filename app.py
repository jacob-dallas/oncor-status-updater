import os
import flask
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)
import requests
from message import MessageAnnouncer, format_sse
import json
import webbrowser
import sys

app = Flask(__name__)
ma = MessageAnnouncer()
base_dir = os.path.dirname(__file__)

@app.route('/')
def index():

    print('Request for index page received')
    return render_template('index.html')

# @app.route('/threaded_update',methods=['POST'])
# def t_update():
#     request.
#     print('updating')
@app.route('/get_data', methods=['GET'])
def get_data():
    with open('power.json') as f:
        data = json.load(f)['Traffic Signals']
    return data

@app.route('/listen', methods=['GET'])
def listen():

    def stream():
        messages = ma.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg

    return flask.Response(stream(), mimetype='text/event-stream')

@app.route('/auth')
def auth():
    code = request.args['code']

    url = 'https://cmss.city.dallastx.cod/rest/ctcapi/v3/auth/token'
    res = requests.get(
        url,
        verify=False,
        params={
            'authCode':code,
            'redirectUri':'https://cmss.city.dallastx.cod/'
        }
    )
    print(res)

    print('Request for index page received')
    return render_template('index.html')



if __name__ == '__main__':
   os.chdir(app.root_path)
   webbrowser.open_new_tab('http://127.0.0.1:5000')
   app.run()
