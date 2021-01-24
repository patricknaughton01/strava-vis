import os
import requests

from flask import Flask
from flask import render_template, session, url_for, request, redirect
app = Flask("strava_vis")

PORT = 5000
CRED_FILE = 'cred.txt'
app.secret_key = os.urandom(32)
with open(CRED_FILE, "r") as cf:
    CLIENT_ID = cf.readline().strip()
    CLIENT_SECRET = cf.readline().strip()


@app.route('/')
def index():
    if 'access_token' not in session:
        return redirect('http://www.strava.com/oauth/authorize?'
            + f'client_id={CLIENT_ID}&response_type=code&'
            + 'redirect_uri='
                + f'http://localhost:{PORT}/{url_for("oauth2_redirect")}&'
            + 'approval_prompt=force&scope=read')
    else:
        print(session['athlete'])
        return 'Logged in'

@app.route('/oauth2-redirect')
def oauth2_redirect():
    code = request.args.get('code')
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    }
    res = requests.post('https://www.strava.com/oauth/token', data=data)
    res_json = res.json()
    session['access_token'] = res_json['access_token']
    session['refresh_token'] = res_json['refresh_token']
    session['expires_at'] = res_json['expires_at']
    session['athlete'] = res_json['athlete']
    return redirect(url_for("index"))
