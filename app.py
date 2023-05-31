import os
import flask
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)
import requests
from message import MessageAnnouncer, format_sse

app = Flask(__name__)
ma = MessageAnnouncer()

@app.route('/')
def index():

    print('Request for index page received')
    return render_template('index.html')

@app.route('/threaded_update',methods=['POST'])
def t_update():
    request.
    print('updating')


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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')

   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = name)
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))


if __name__ == '__main__':
   app.run()
