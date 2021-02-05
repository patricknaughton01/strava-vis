import os
import requests
import numpy as np
import io
import json
import pickle
import math
import datetime as dt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

from flask import Flask
from flask import render_template, session, url_for, request, redirect
from flask import Response
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
app = Flask("strava_vis")

PORT = 5000
CRED_FILE = 'cred.txt'
API_PREFIX = 'https://www.strava.com/api/v3'
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
        auth_header = headers={'Authorization':
            f'Bearer {session["access_token"]}'}
        id = session['athlete']['id']
        stats = json.loads(requests.get(API_PREFIX
            + f"/athletes/{id}/stats", headers=auth_header).text)
        run_count = stats['all_run_totals']['count']
        max_reads = 100
        file_dir = f'user_data/{CLIENT_ID}/'
        file_name = 'activities.p'
        path = file_dir + file_name
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
            all_activities = load_activities(run_count, max_reads, auth_header)
            with open(path, 'wb') as af:
                pickle.dump(all_activities, af)
        else:
            with open(path, 'rb') as af:
                acts = pickle.load(af)
            if len(acts) == 0:
                all_activities = load_activities(run_count, max_reads,
                    auth_header)
                with open(path, 'wb') as af:
                    pickle.dump(all_activities, af)
            else:
                new_activities = []
                latest = acts[0]
                latest_time = str(latest['start_date'])
                latest_time = '2021-02-04T14:55:27Z'
                latest_time = dt.datetime.strptime(latest_time,
                    '%Y-%m-%dT%H:%M:%SZ').timestamp()
                page = 1
                while True:
                    activities = requests.get(API_PREFIX
                        + '/athlete/activities', headers=auth_header,
                        params={'page': page, 'per_page': max_reads,
                        'after': latest_time})
                    activities = json.loads(activities.text)
                    new_activities.extend(activities)
                    page += 1
                    if len(activities) == 0:
                        break
                new_activities.extend(acts)
                with open(path, 'wb') as af:
                    pickle.dump(new_activities, af)
        session["a_file"] = path
        return render_template('index.html')


@app.route('/total_dist.svg')
def total_dist_svg():
    # https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    fig = Figure(tight_layout=True)
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
    strava_orange = '#fc4c02'
    ax.plot(x, y, color=strava_orange, marker='.')
    ax.fill_between(x, y, color=strava_orange, alpha=0.5)
    ax.set_xlabel('Date')
    date_formatter = mdates.DateFormatter('%Y-%m-%d')
    lower_lim_x = x[0]
    upper_lim_x = x[-1]
    x_buffer = 0.05
    width = upper_lim_x - lower_lim_x
    lower_lim_x -= x_buffer * width
    upper_lim_x += x_buffer * width
    ax.set_xlim(lower_lim_x, upper_lim_x)
    x_ticks = ax.get_xticks().tolist()
    ax.xaxis.set_major_locator(mticker.FixedLocator(x_ticks))
    ax.set_xticklabels(x_ticks, rotation=45)
    ax.xaxis.set_major_formatter(date_formatter)
    ax.set_ylabel('Distance (Miles)')
    y_buffer = 0.1
    top_lim_y = (1 + y_buffer) * y[-1]
    ax.set_ylim(0, top_lim_y)

    gray = "#808080"
    ax.plot([lower_lim_x, upper_lim_x], [y[-1], y[-1]], color=gray,
        linestyle='--', alpha=0.5)
    text_gap_x = 1
    text_gap_y = 1
    pt = (lower_lim_x, y[-1])
    figure_pt = (pt[0] + text_gap_x, pt[1] + text_gap_y)
    ax.annotate(f"{round(y[-1], 1)} Miles", pt, xytext=figure_pt)

    ax.set_title('Total Distance')

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


def load_activities(run_count, max_reads, auth_header):
    all_activities = []
    for i in range(math.ceil(run_count / max_reads)):
        activities = requests.get(API_PREFIX
            + '/athlete/activities', headers=auth_header,
            params={'page': i+1, 'per_page': max_reads})
        all_activities.extend(json.loads(activities.text))
    return all_activities


def meters_to_miles(x):
    return x * 0.000621371


if __name__ == "__main__":
    app.run(debug=True)
