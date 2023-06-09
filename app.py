import os
import flask
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)
import requests
from message import MessageAnnouncer, format_sse
import json
import webbrowser
from threaded_update import UpdateThread
import datetime
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading
import queue

app = Flask(__name__)
base_dir = os.path.dirname(__file__)
queue_outage = queue.Queue(6)

@app.route('/')
def index():

    print('Request for index page received')
    return render_template('index.html')

@app.route('/threaded_update',methods=['POST'])
def t_update():
    print('updating')


@app.route('/get_data', methods=['GET'])
def get_data():
    with open('power.json') as f:
        data = json.load(f)['Traffic Signals']
    return data

@app.route('/listen', methods=['GET'])
def listen():

    def stream():
        while True:
            msg = queue_outage.get()  # blocks until a new message arrives
            if "modem" in msg:
                yield format_sse(msg,'ping')
            else :
                yield format_sse(msg)


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

    with open('power.json','r') as f:
        meters = json.load(f)

        
    outage_log = open('outage_log.txt','w')
    UpdateThread.sig_meters = meters['Traffic Signals']
    UpdateThread.meters = meters
    UpdateThread.outage_log = outage_log
    
    UpdateThread.n_meters = len(UpdateThread.sig_meters)
    n_threads = 3 
    threads = []
    for thread in range(n_threads):
        thread_i = UpdateThread(queue_outage)
        threads.append(thread_i)
        thread_i.start()
        


    webbrowser.open_new_tab('http://127.0.0.1:5000')
    app.run()


    # have databases, config and text files in appdata
    # readme in distribution