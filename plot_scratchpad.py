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
    text_gap = 1
    pt = (lower_lim_x, y[-1])
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    ax_width, ax_height = bbox.width, bbox.height
    ax_width_pts = ax_width * 72
    ax_height_pts = ax_height * 72
    ax_pos = ax.get_position()
    left, bottom, right, top = ax_pos.x0, ax_pos.y0, ax_pos.x1, ax_pos.y1
    figure_pt = (12, ax_height_pts)# * (top - bottom) * y[-1] / top_lim_y)
    print(figure_pt)
    ax.annotate(f"{round(y[-1], 1)} Miles", pt, xytext=figure_pt, xycoords="axes points")

    ax.set_title('Total Distance')
    plt.show()


if __name__ == "__main__":
    main()
