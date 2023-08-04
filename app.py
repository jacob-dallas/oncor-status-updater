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
from model import Signal, Network
from json_to_excel import import_from_excel

data_root = os.path.join(os.getenv('APPDATA'),'acid')
db_path = os.path.join(data_root,'db.json')
modem_db_path = os.path.join(data_root,'modem_db.json')
log_dir = os.path.join(data_root,'logs')
env_path = os.path.join(data_root,'.env')
oncor_log = os.path.join(log_dir,'oncor.txt')
base_dir = os.path.dirname(__file__)


app = Flask(__name__)
if not os.path.exists(data_root):
    os.mkdir(data_root)
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

if not os.path.exists(env_path):
    shutil.copy('.env-template',env_path)

dotenv.load_dotenv(env_path)

app.secret_key=os.environ['SESSION_KEY']
log_dir=os.environ.get('LOGDIR',log_dir)

from threaded_update import DBCounter,UpdateThread
from power_thread import PowerThread,n_power_updaters
from radar_thread import RadarThread,n_radar_updaters
from modem_thread import ModemThread,n_modem_updaters

# Give threads the basic info they need
sig_db = Signal(path=db_path)
net_db = Network(path=modem_db_path)

ModemThread.signals = sig_db
UpdateThread.log_dir = log_dir


#################################################################################
##############################    Page Routes    ################################
#################################################################################


@app.route('/')
def index():
    if n_power_updaters():
        power_status = 'Online'
        buttons= ['display:none;','display:block;']
    else:
        power_status = 'Offline'
        buttons= ['display:block;','display:none;']

    n_threads = n_power_updaters()

    return render_template(
        'index.html',
        power_status=power_status,
        n_threads=n_threads,
        buttons=buttons
    )


@app.route('/power')
def power():
    return render_template('power.html')


@app.route('/radar')
def radar():
    return render_template('radar.html')


@app.route('/modem')
def modem():
    return render_template('modem.html')


@app.route('/passed')
def passed():
    return render_template('stable_communication.html')


@app.route('/wip')
def progress():
    return render_template('wip.html')


@app.route('/db_manager')
def db_manager():
    return render_template('db_manager.html')


#################################################################################
##############################     Services      ################################
#################################################################################

@app.route('/get_data', methods=['GET'])
def get_data():
    return sig_db.get_data()


@app.route('/get_radar_data', methods=['GET'])
def get_radar_data():
    return sig_db.get_data()


@app.route('/get_modem_data', methods=['GET'])
def get_modem_data():
    return net_db.get_data()


@app.route('/get_pf_table', methods=['GET'])
def get_pf_table():
    ip = request.args.get('ip')
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        res = requests.post(url,data=data,timeout=4)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        url = f"http://{ip}:8080/api/config/firewall/portfwd/"

        res = requests.get(url,cookies=cookies,timeout=4)
        if res.status_code==401:
            return {'ip':ip,'modem':'not authorized'}
        ports = res.json()['data']
        return ports

    except Exception as e:
        return {}


@app.route('/add_pf_table', methods=['POST'])
def add_pf_table():
    data = request.get_json()
    ip = data.get('ip')
    ip_loc = data.get('ip_loc')
    name = data.get('name')
    int_port_start = data.get('int_port_start')
    int_port_end = data.get('int_port_end')
    loc_port = data.get('loc_port')
    protocol = data.get('protocol')
    enable = data.get('enable')

    enable_mapping = {'true':True,'1':True,'0':False,'false':False}
    enable=enable_mapping.get(enable)
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        res = requests.post(url,data=data,timeout=4)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        url = f"http://{ip}:8080/api/config/firewall/portfwd/"
        xrsf = res.cookies.get_dict(domain=ip)['_xsrf']
        res = requests.post(
            url,
            cookies=cookies,
            timeout=4,
            params={
                'data':json.dumps(
                    {
                        'protocol':protocol,
                        'enabled':enable, 
                        'name':name,
                        'wan_port_start':int(int_port_start),
                        'wan_port_end':int(int_port_end),
                        'ip_address':ip_loc,
                        'lan_port_offt':int(loc_port),
                    },
                    separators=(',', ':')
                )
            },
            data={
                        'protocol':protocol,
                        'enabled':enable, 
                        'name':name,
                        'wan_port_start':int(int_port_start),
                        'wan_port_end':int(int_port_end),
                        'ip_address':ip_loc,
                        'lan_port_offt':int(loc_port),
            },
            headers={
                'Content-Type': 'application/json',
                'X-Csrftoken':xrsf
            }
        )
        if res.status_code==401:
            return {'ip':ip,'modem':'not authorized'}
        ind = res.json()['data']
        return {'ind':ind}

    except Exception as e:
        return {}


@app.route('/edit_pf_table', methods=['PUT'])
def edit_pf_table():
    data = request.get_json()
    ip = data.get('ip')
    ip_loc = data.get('ip_loc')
    name = data.get('name')
    int_port_start = data.get('int_port_start')
    int_port_end = data.get('int_port_end')
    loc_port = data.get('loc_port')
    protocol = data.get('protocol','both')
    enable = data.get('enable',True)
    ind = data.get('ind')
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        res = requests.post(url,data=data,timeout=4)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)
        xrsf = res.cookies.get_dict(domain=ip)['_xsrf']

        url = f"http://{ip}:8080/api/config/firewall/portfwd/{ind}"

        res = requests.put(
            url,
            cookies=cookies,
            timeout=4,
            params={
                'data':json.dumps(
                    {
                        'protocol':protocol,
                        'enabled':enable, 
                        'name':name,
                        'wan_port_start':int(int_port_start),
                        'wan_port_end':int(int_port_end),
                        'ip_address':ip_loc,
                        'lan_port_offt':int(loc_port),
                    },
                    separators=(',', ':')
                )
            },
            headers={
                'Content-Type': 'application/json',
                'X-Csrftoken':xrsf
            }
        )
        if res.status_code==401:
            return {'ip':ip,'modem':'not authorized'}
        updates = res.json()['data']
        return updates

    except Exception as e:
        return {}


@app.route('/del_pf_table', methods=['DELETE'])
def del_pf_table():
    ip = request.args.get('ip')
    ind = request.args.get('ind')
    url = f"http://{ip}:8080/login/"
    data = {
    'cprouterusername': os.environ['CP_USER'],
    'cprouterpassword': os.environ['CP_PASS']
    }
    try:
        res = requests.post(url,data=data,timeout=4)
        cookie_1 = res.history[0].cookies.get_dict(domain=ip)
        cookies = requests.utils.add_dict_to_cookiejar(res.cookies,cookie_1)

        xrsf = res.cookies.get_dict(domain=ip)['_xsrf']
        url = f"http://{ip}:8080/api/config/firewall/portfwd/{ind}"

        res = requests.delete(
            url,
            cookies=cookies,
            timeout=4,
            params={'data':int(ind)},
            headers={
                'Content-Type': 'application/json',
                'X-Csrftoken':xrsf
            }
            )
        if res.status_code==401:
            return {'ip':ip,'modem':'not authorized'}
        status = res.json()['data']
        return {'status':status}

    except Exception as e:
        return {}
    

#################################################################################
##############################     Monitors      ################################
#################################################################################


@app.route('/monitor_threads')
def monitor_thread():
    def stream():
        while (n_power_updaters() or n_radar_updaters() or n_modem_updaters()):                
            yield format_sse(f'{n_power_updaters()}','power_thread_count')
            yield format_sse(f'{n_radar_updaters()}','radar_thread_count')
            yield format_sse(f'{n_modem_updaters()}','modem_thread_count')
            time.sleep(2)
        yield format_sse(f'','close')

    return flask.Response(stream(), mimetype='text/event-stream')


@app.route('/pause_listen', methods=['POST'])
def puase_listen():
    if n_power_updaters():
        PowerThread.pauser.set()
    return flask.Response(status=200)


@app.route('/pause_radar_listen', methods=['POST'])
def puase_radar_listen():
    if n_radar_updaters():
        RadarThread.pauser.set()
    return flask.Response(status=200)


@app.route('/pause_modem_listen', methods=['POST'])
def puase_modem_listen():
    if n_modem_updaters():
        ModemThread.pauser.set()
    return flask.Response(status=200)


@app.route('/listen', methods=['GET'])
def listen():
    if n_power_updaters():
        PowerThread.pauser.clear()
    def stream():
        cond = True
        while cond:
            try:
                msg = PowerThread.q.get(timeout=60) 
                if "modem" in msg:
                    yield format_sse(msg,'ping_comm')
                elif 'time' in msg:
                    yield format_sse(msg,'timestamp')
                else :
                    yield format_sse(msg,'oncor')
            except Exception as e:
                cond=False

    return flask.Response(stream(), mimetype='text/event-stream')


@app.route('/radar_listen', methods=['GET'])
def radar_listen():
    if n_radar_updaters():
        RadarThread.pauser.clear()
    def stream():
        cond = True
        while cond:
            try:
                msg = RadarThread.q.get(timeout=60) 
                if "modem" in msg:
                    yield format_sse(msg,'ping_comm')
                elif 'time' in msg:
                    yield format_sse(msg,'timestamp')
                else :
                    yield format_sse(msg,'radar')
            except Exception as e:
                cond=False
    return flask.Response(stream(), mimetype='text/event-stream')


@app.route('/modem_listen', methods=['GET'])
def modem_listen():
    if n_modem_updaters():
        ModemThread.pauser.clear()
    def stream():
        cond = True
        while cond:
            try:
                msg = ModemThread.q.get(timeout=60) 
                if '\"msg_id\":\"time\"' in msg:
                    yield format_sse(msg,'timestamp')
                else :
                    yield format_sse(msg,'modem')
            except Exception as e:
                cond=False
    return flask.Response(stream(), mimetype='text/event-stream')


#################################################################################
##############################     Functions     ################################
#################################################################################


@app.route('/stop_threads', methods=['POST'])
def stop_threads():
    if request.args.get('thread')=='power':
        PowerThread.stopper.set()
    if request.args.get('thread')=='radar':
        RadarThread.stopper.set()
    if request.args.get('thread')=='modem':
        ModemThread.stopper.set()
    return flask.Response(status=200)


def start_update_thread(req_data,thread_type):
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

    q = queue.Queue(20)
    counter= DBCounter()
    stopper = threading.Event()
    pauser = threading.Event()
    if thread_type == ModemThread:
        db = net_db
    else:
        db = sig_db
    threads = []

    thread_type.counter=counter
    thread_type.stopper=stopper
    thread_type.pauser=pauser
    thread_type.q=q

    for thread in range(int(n_threads)):
        thread_i = thread_type(
            db,
            counter,
            stopper,
            q,
            pauser
        )
        threads.append(thread_i)
        thread_i.start()


@app.route('/start_power_threads', methods=['POST'])
def start_power_threads():
    if n_power_updaters():
        return flask.Response(status=400)

    print(request.form)
    req_data = request.form
    start_update_thread(req_data,PowerThread)
    
    return flask.Response(status=200)


@app.route('/start_radar_threads', methods=['POST'])
def start_radar_threads():
    if n_radar_updaters():
        return flask.Response(status=400)

    print(request.form)
    req_data = request.form
    start_update_thread(req_data,RadarThread)
    
    return flask.Response(status=200)

@app.route('/start_modem_threads', methods=['POST'])
def start_modem_threads():
    if n_modem_updaters():
        return flask.Response(status=400)

    print(request.form)
    req_data = request.form
    start_update_thread(req_data,ModemThread)
    
    return flask.Response(status=200)


#################################################################################
##############################        Auth       ################################
#################################################################################

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

#################################################################################
##############################      Exp/Imp      ################################
#################################################################################


@app.route('/update_from_input', methods = ['POST'])
def update_from_input():
    data = request.form
    with sig_db.lock:
        for signal in sig_db.data:
            if signal['cog_id']==int(data['cog_id']):
                for k,v in data.items():
                    if k=='cog_id':
                        continue
                    else:
                        signal[k]=v
    sig_db.save_to_file()
    return flask.Response(status=200)


@app.route('/get_xlsx', methods=['POST'])
def get_xlsx():
    db_type = request.args.get('type')
    fields = request.json
    db_map = {
        'network':net_db,
        'signals':sig_db
    }
    file = db_map[db_type].export(fields)
    return send_file(file,download_name='data.xlsx',mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route('/post_xlsx', methods=['POST'])
def post_xlsx():
    file = request.files['file']
    db_type = request.args.get('type')
    db_map = {
        'network':net_db,
        'signals':sig_db
    }
    db = import_from_excel(file,db_map[db_type])
    return redirect(url_for('db_manager'))



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
            serve(app, host=ip, port=port,threads=20)

