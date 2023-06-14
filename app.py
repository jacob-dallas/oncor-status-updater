from wakepy import keep
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
        data = json.load(f)
    return data

@app.route('/listen', methods=['GET'])
def listen():

    def stream():
        while True:
            msg = queue_outage.get()  # blocks until a new message arrives
            if "modem" in msg:
                yield format_sse(msg,'ping_comm')
            elif 'time' in msg:
                yield format_sse(msg,'timestamp')
            else :
                yield format_sse(msg,'oncor')


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
    with keep.presenting() as m:
        os.chdir(app.root_path)

        with open('power.json','r') as f:
            signals = json.load(f)

            
        outage_log = open('outage_log.txt','w')
        UpdateThread.signals = signals
        UpdateThread.outage_log = outage_log
        
        UpdateThread.n_meters = len(UpdateThread.signals)
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