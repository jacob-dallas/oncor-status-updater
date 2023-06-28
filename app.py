from wakepy import keep
import os
import sys
import shutil
import flask
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for,send_file)
import requests
from message import format_sse
import json
import webbrowser
from threaded_update import UpdateThread
import queue
import pandas as pd
import io
from json_to_excel import export_sig, import_sig
import threading
import time

app = Flask(__name__)
base_dir = os.path.dirname(__file__)
queue_outage = queue.Queue(6)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/power')
def power():
    return render_template('power.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    with UpdateThread.lock:
        data = UpdateThread.signals
    return data

@app.route('/get_xlsx', methods=['GET'])
def get_xlsx():
    with UpdateThread.lock:
        data = UpdateThread.signals
    file = export_sig(data)
    return send_file(file,download_name='signals.xlsx',mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/post_xlsx', methods=['POST'])
def post_xlsx():
    file = request.files['file']
    signals = import_sig(file)
    with UpdateThread.lock:
        UpdateThread.signals = signals
    return redirect(url_for('power'))

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


@app.route('/wip')
def progress():
    return render_template('wip.html')

@app.route('/start_power_threads')
def power_thread():
    data_root = os.path.join(os.getenv('APPDATA'),'acid')
    db_path = os.path.join(data_root,'db.json')
    log_dir = os.path.join(data_root,'logs')
    oncor_log = os.path.join(log_dir,'oncor.txt')

    if not os.path.exists(data_root):
        os.mkdir(data_root)
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    if not os.path.exists(db_path):
        shutil.copy('power.json',db_path)

    with open(db_path,'r') as f:
        signals = json.load(f)

    # outage_log = open(oncor_log,'w')
    # UpdateThread.signals = signals
    # UpdateThread.outage_log = outage_log
    # UpdateThread.db = db_path
    # UpdateThread.data_root = data_root
    
    # UpdateThread.n_meters = len(UpdateThread.signals)
    # n_threads = 10
    # threads = []
    # for thread in range(n_threads):
    #     thread_i = UpdateThread(queue_outage)
    #     threads.append(thread_i)
    #     thread_i.start()

    cond = True
    def stream():
        while cond:
            yield format_sse(f'{threading.active_count()}','thread_count')
            time.sleep(2)

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
    return render_template('index.html')



if __name__ == '__main__':
    data_root = os.path.join(os.getenv('APPDATA'),'acid')
    db_path = os.path.join(data_root,'db.json')
    log_dir = os.path.join(data_root,'logs')
    oncor_log = os.path.join(log_dir,'oncor.txt')

    if not os.path.exists(data_root):
        os.mkdir(data_root)
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    if not os.path.exists(db_path):
        shutil.copy('power.json',db_path)

    with open(db_path,'r') as f:
        signals = json.load(f)
    
    with keep.presenting() as m:

        outage_log = open(oncor_log,'w')
        UpdateThread.signals = signals
        UpdateThread.outage_log = outage_log
        UpdateThread.db = db_path
        UpdateThread.data_root = data_root
        
        UpdateThread.n_meters = len(UpdateThread.signals)
        n_threads = 10
        threads = []
        for thread in range(n_threads):
            thread_i = UpdateThread(queue_outage)
            threads.append(thread_i)
            thread_i.start()
            


        webbrowser.open_new_tab('http://127.0.0.1:5000')
        app.run()


        # have databases, config and text files in appdata
        # readme in distribution