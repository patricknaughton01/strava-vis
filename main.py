import os
import requests
import numpy as np
import io
import json
import pickle
import matplotlib.dates as mdates

from flask import Flask
from flask import render_template, session, url_for, request, redirect
from flask import Response
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
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
            + 'approval_prompt=force&scope=activity:read')
    else:
        activities = requests.get('https://www.strava.com/api/v3'
            + '/athlete/activities',
            headers={'Authorization': f'Bearer {session["access_token"]}'})
        file_dir = f'user_data/{CLIENT_ID}/'
        file_name = 'activities.p'
        path = file_dir + file_name
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(path, 'wb') as af:
            pickle.dump(json.loads(activities.text), af)
        session["a_file"] = path
        return render_template('index.html')


@app.route('/total_dist.svg')
def total_dist_svg():
    # https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    x = []
    y = []
    a_file = session["a_file"]
    with open(a_file, 'rb') as af:
        acts = pickle.load(af)
    for i in range(len(acts)-1, -1, -1):
        x.append(mdates.date2num([acts[i]['start_date']])[0])
        dist = meters_to_miles(acts[i]['distance'])
        if len(y) > 0:
            y.append(y[-1] + dist)
        else:
            y.append(dist)
    ax.plot_date(x, y, fmt='-')
    ax.set_xlabel('Date')
    ax.set_ylabel('Distance (Miles)')
    output = io.BytesIO()
    FigureCanvasSVG(fig).print_svg(output)
    return Response(output.getvalue(), mimetype="image/svg+xml")


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


def meters_to_miles(x):
    return x * 0.000621371


if __name__ == "__main__":
    app.run(debug=True)
