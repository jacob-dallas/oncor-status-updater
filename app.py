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
from threaded_update import UpdateThread,n_power_updaters,stop_power
import queue
import pandas as pd
import io
from json_to_excel import export_sig, import_sig
import threading
import time
import datetime
from waitress import serve
import dotenv
dotenv.load_dotenv()

data_root = os.path.join(os.getenv('APPDATA'),'acid')
db_path = os.path.join(data_root,'db.json')
log_dir = os.path.join(data_root,'logs')
oncor_log = os.path.join(log_dir,'oncor.txt')
app = Flask(__name__)
base_dir = os.path.dirname(__file__)
queue_outage = queue.Queue(6)

@app.route('/')
def index():
    if n_power_updaters():
        power_status = 'Online'
        buttons= ['display:none;','display:block;']
    else:
        power_status = 'Offline'
        buttons= ['display:block;','display:none;']

    n_threads = n_power_updaters()

    return render_template('index.html',power_status=power_status,n_threads=n_threads,buttons=buttons)

@app.route('/power')
def power():
    return render_template('power.html')

@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        with UpdateThread.lock:
            data = UpdateThread.signals
    except AttributeError:
        with open(db_path,'r') as f:
            data = json.load(f)
            with UpdateThread.lock:
                UpdateThread.signals = data
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

@app.route('/pause_listen', methods=['POST'])
def puase_listen():
    req_data = request.form
    print(req_data)
    with UpdateThread.lock:
        UpdateThread.pause= True
    return flask.Response(status=200)

@app.route('/listen', methods=['GET'])
def listen():
    print('new listen!')
    with UpdateThread.lock:
        UpdateThread.pause = False
    # why are so many threads being generated
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

@app.route('/stop_power_threads', methods=['POST'])
def stop_power_threads():
    stop_power()
    return flask.Response(status=200)

@app.route('/start_power_threads', methods=['POST'])
def start_power_threads():
    if n_power_updaters():
        return flask.Response(status=400)

    print(request.form)
    req_data = request.form

    record = req_data.get('recordInt',0)
    n_threads = req_data.get('threads',10)
    stop_after = req_data.get('runFor', 0)
    stop_at = req_data.get('runUntil',0)
    pause = req_data.get('pause',True)



    if stop_at:
        stop_at = datetime.datetime.fromisoformat(stop_at)
    if stop_after:
        stop_at = datetime.datetime.now() + datetime.timedelta(hours=float(stop_after))

    if not os.path.exists(data_root):
        os.mkdir(data_root)
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    if not os.path.exists(db_path):
        shutil.copy('power.json',db_path)

    with open(db_path,'r') as f:
        signals = json.load(f)

    outage_log = open(oncor_log,'w')
    UpdateThread.pause=pause
    UpdateThread.signals = signals
    UpdateThread.outage_log = outage_log
    UpdateThread.db = db_path
    UpdateThread.data_root = data_root
    UpdateThread.stop_at = stop_at
    UpdateThread.record = record

    UpdateThread.n_signals = len(UpdateThread.signals)
    threads = []
    for thread in range(n_threads):
        thread_i = UpdateThread(queue_outage)
        threads.append(thread_i)
        thread_i.start()
    return flask.Response(status=200)

@app.route('/monitor_power_threads')
def power_thread():
    cond = True
    def stream():
        while cond:                
            yield format_sse(f'{n_power_updaters()}','thread_count')
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
    
    with keep.presenting() as m:
        

        if os.environ['DEVELOPMENT']:
            webbrowser.open_new_tab('http://127.0.0.1:5000')
            app.run(debug=True)
        else:
            serve(app, host='0.0.0.0', port=5000)