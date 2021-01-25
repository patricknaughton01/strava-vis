import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

from main import meters_to_miles


def main():
    fig = plt.figure(tight_layout=True)
    ax = fig.add_subplot(1, 1, 1)
    x = []
    y = []
    with open("user_data/60483/activities.p", 'rb') as af:
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
    x_ticks = ax.get_xticks().tolist()
    ax.xaxis.set_major_locator(mticker.FixedLocator(x_ticks))
    ax.set_xticklabels(x_ticks, rotation=45)
    ax.xaxis.set_major_formatter(date_formatter)
    ax.set_yticks(list(ax.get_yticks()) + [y[-1]])
    ax.set_ylabel('Distance (Miles)')
    ax.set_title('Total Distance')
    plt.show()


if __name__ == "__main__":
    main()
