from wakepy import keep
import os
import shutil
import flask
from flask import (Flask, redirect, render_template, request, session,
                   send_from_directory, url_for,send_file)
import requests
from message import format_sse
import json
import webbrowser
import queue
import pandas as pd
import io
import threading
import time
import datetime
from waitress import serve
import dotenv

data_root = os.path.join(os.getenv('APPDATA'),'acid')
db_path = os.path.join(data_root,'db.json')
log_dir = os.path.join(data_root,'logs')
env_path = os.path.join(data_root,'.env')
oncor_log = os.path.join(log_dir,'oncor.txt')
app = Flask(__name__)
base_dir = os.path.dirname(__file__)
queue_outage = queue.Queue(20)
queue_radar = queue.Queue(20)

if not os.path.exists(data_root):
    os.mkdir(data_root)
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

if not os.path.exists(db_path):
    shutil.copy('db_template',db_path)

if not os.path.exists(env_path):
    shutil.copy('.env-template',env_path)

dotenv.load_dotenv(env_path)
app.secret_key=os.environ['SESSION_KEY']
from json_to_excel import export_sig, import_sig
from threaded_update import UpdateThread,n_power_updaters,stop_power
from radar_thread import RadarThread,n_radar_updaters,stop_radar

with open(db_path,'r') as f:
    signals = json.load(f)

outage_log = open(oncor_log,'w')

UpdateThread.signals = signals
UpdateThread.outage_log = outage_log
UpdateThread.db = db_path
UpdateThread.data_root = data_root
UpdateThread.n_signals = len(UpdateThread.signals)

RadarThread.signals = signals
RadarThread.log = outage_log
RadarThread.db = db_path
RadarThread.data_root = data_root
RadarThread.n_signals = len(RadarThread.signals)

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
@app.route('/radar')
def radar():
    return render_template('radar.html')

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
@app.route('/get_radar_data', methods=['GET'])
def get_radar_data():
    try:
        with RadarThread.lock:
            data = RadarThread.signals
    except AttributeError:
        with open(db_path,'r') as f:
            data = json.load(f)
            with RadarThread.lock:
                RadarThread.signals = data
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
        shutil.copy(UpdateThread.db,os.path.join(UpdateThread.data_root,'signals.bak'))
        with open(UpdateThread.db,'w') as f:
            json.dump(UpdateThread.signals,f)
    return redirect(url_for('power'))

@app.route('/pause_listen', methods=['POST'])
def puase_listen():
    req_data = request.form
    print(req_data)
    with UpdateThread.lock:
        UpdateThread.pause= True
    return flask.Response(status=200)
@app.route('/pause_radar_listen', methods=['POST'])
def puase_radar_listen():
    req_data = request.form
    print(req_data)
    with RadarThread.lock:
        RadarThread.pause= True
    return flask.Response(status=200)

@app.route('/listen', methods=['GET'])
def listen():
    print('new listen!')
    with UpdateThread.lock:
        UpdateThread.pause = False
    # why are so many threads being generated
    def stream():
        cond = True
        while cond:
            try:
                msg = queue_outage.get(timeout=2) 
                if "modem" in msg:
                    yield format_sse(msg,'ping_comm')
                elif 'time' in msg:
                    yield format_sse(msg,'timestamp')
                else :
                    yield format_sse(msg,'oncor')
            except Exception as e:
                cond=False
        print('closing listen!')


    return flask.Response(stream(), mimetype='text/event-stream')

@app.route('/radar_listen', methods=['GET'])
def radar_listen():
    with RadarThread.lock:
        RadarThread.pause = False
    # why are so many threads being generated
    def stream():
        cond = True
        while cond:
            try:
                msg = queue_radar.get(timeout=20) 
                if "modem" in msg:
                    yield format_sse(msg,'ping_comm')
                elif 'time' in msg:
                    yield format_sse(msg,'timestamp')
                else :
                    yield format_sse(msg,'radar')
            except Exception as e:
                cond=False


    return flask.Response(stream(), mimetype='text/event-stream')


@app.route('/wip')
def progress():
    return render_template('wip.html')

@app.route('/stop_threads', methods=['POST'])
def stop_threads():
    if request.args.get('thread')=='power':
        stop_power()
    if request.args.get('thread')=='radar':
        stop_radar()
    return flask.Response(status=200)

def start_update_thread(req_data,thread_type,queue_loc):
    record = req_data.get('recordInt',0)
    n_threads = req_data.get('nThread',10)
    stop_after = req_data.get('runFor', 0)
    stop_at = req_data.get('runUntil',0)
    pause = req_data.get('pause',True)



    if stop_at:
        stop_at = datetime.datetime.fromisoformat(stop_at)
    if stop_after:
        stop_at = datetime.datetime.now() + datetime.timedelta(hours=float(stop_after))



    thread_type.pause=pause
    thread_type.stop_at = stop_at
    thread_type.record = record
    
    threads = []
    for thread in range(int(n_threads)):
        thread_i = thread_type(queue_loc)
        threads.append(thread_i)
        thread_i.start()


@app.route('/start_power_threads', methods=['POST'])
def start_power_threads():
    if n_power_updaters():
        return flask.Response(status=400)

    print(request.form)
    req_data = request.form
    start_update_thread(req_data,UpdateThread,queue_outage)
    
    return flask.Response(status=200)

@app.route('/start_radar_threads', methods=['POST'])
def start_radar_threads():
    if n_radar_updaters():
        return flask.Response(status=400)

    print(request.form)
    req_data = request.form
    start_update_thread(req_data,RadarThread,queue_radar)
    
    return flask.Response(status=200)

@app.route('/monitor_threads')
def monitor_thread():
    def stream():
        while (n_power_updaters() or n_radar_updaters()):                
            yield format_sse(f'{n_power_updaters()}','power_thread_count')
            yield format_sse(f'{n_radar_updaters()}','radar_thread_count')
            time.sleep(2)
        yield format_sse(f'','close')

    return flask.Response(stream(), mimetype='text/event-stream')

@app.route('/update_from_input', methods = ['POST'])
def update_from_input():
    data = request.form
    with UpdateThread.lock:
        for signal in UpdateThread.signals:
            if signal['cog_id']==int(data['cog_id']):
                for k,v in data.items():
                    if k=='cog_id':
                        continue
                    else:
                        signal[k]=v
    with RadarThread.lock:
        for signal in RadarThread.signals:
            if signal['cog_id']==int(data['cog_id']):
                for k,v in data.items():
                    if k=='cog_id':
                        continue
                    else:
                        signal[k]=v
        with open(RadarThread.db,'w') as f:
                json.dump(RadarThread.signals,f,indent=4)
    return flask.Response(status=200)
@app.route('/auth')
def auth():
    tenant = os.environ['AAD_TENANT']
    client = os.environ['AAD_CLIENT']
    return redirect(f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?client_id={client}&response_type=code&scope=https://ericomm.onmicrosoft.com/ab34a501-302c-4972-a8e2-ebe14334f9e0/user_impersonation')

@app.route('/auth_code')
def auth_code():
    code = request.args.get('code')
    tenant = os.environ['AAD_TENANT']
    client = os.environ['AAD_CLIENT']
    res = requests.post(
        f'https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token',
        headers={'Content-Type':'application/x-www-form-urlencoded'},
        data={
            'client_id':client,
            'code':code,
            'grant_type':'authorization_code',
            'redirect_uri':'http://127.0.0.1:5000/auth_code'
        }
    )
    session['cut'] = json.loads(res.text)

    return render_template('index.html')

if __name__ == '__main__':
    ip = os.environ['HOSTIP']
    port = os.environ['HOSTPORT']
    with keep.presenting() as m:
        

        if os.environ['DEVELOPMENT']=='True':
            # print(os.getcwd())
            # os.chdir(app.root_path)
            # time.sleep(30)
            app.run(debug=True)
        else:
            url = f'http://{ip}:{port}'
            webbrowser.open_new_tab(url)
            serve(app, host=ip, port=port,)

