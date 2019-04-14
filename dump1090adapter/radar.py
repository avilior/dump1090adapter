import matplotlib.pyplot as plt
import numpy as np
import time
from geographiclib.geodesic import Geodesic

text_style = dict(horizontalalignment='center', verticalalignment='center', fontsize=8, fontdict={'family':'monospace'})


class Radar():
    def __init__(self, fig, rowcol, lat, lon, range=None):
        self.tracks = {}
        self.fig = fig
        self.ax = plt.subplot(rowcol, projection='polar')
        self.ax.set_theta_zero_location('N') # set zero to North
        self.ax.set_theta_direction(-1)
        self.lat = lat
        self.lon = lon
        self.range = range
        if self.range is not None:
            self.ax.set_ylim(0, self.range)

    def compute_bearing_vector(self, lat, lon):
        # compute heading and bearing from the site
        bearing_vector = Geodesic.WGS84.Inverse(self.lat, self.lon, lat, lon)
        range = bearing_vector['s12'] / 1e3
        bearing = bearing_vector['azi1']
        if bearing < 0:
            bearing = 360 + bearing
        return bearing, range

    def refresh(self):
        # do we need to redimention
        self.ax.relim()
        self.ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.2)  # now i dont need this?

    def update_track(self, track_name: str, lat: float, lon: float):

        # compute heading and bearing from the site
        bearing, range = self.compute_bearing_vector(lat, lon)

        if self.range != None and range > self.range:
            self.remove_track(track_name)
            return


        try:
            # convert bearing to radian
            # bearing_as_radian = bearing * np.pi / 180.0
            bearing_as_radian = np.radians(bearing)

            track = self.tracks[track_name] if track_name in self.tracks else None

            if track is None:
                #print(F"Adding {track_name} to radar")
                track_line, = self.ax.plot(bearing_as_radian, range, ".")
                # track_text = ax.text(bearing_as_radian, range, track_name, withdash = True, dashdirection=1, dashlength=20, dashpush=10)
                track_text = self.ax.text(bearing_as_radian, range, track_name, **text_style, withdash=True, dashlength=20, dashpush=5, dashpad=5)
                # track_text = ax.annotate(track_name, xy=(bearing_as_radian,range), xycoords='data', xytext=(bearing_as_radian,range), textcoords='data', verticalalignment='bottom', horizontalalignment='center' )
                self.tracks[track_name] = {'track_line': track_line, 'track_text': track_text}
            else:
                track_line = track['track_line']
                track_text = track['track_text']
                xdata = track_line.get_xdata()
                ydata = track_line.get_ydata()

                xdata = np.insert(xdata, -1, bearing_as_radian)
                ydata = np.insert(ydata, -1, range)
                track_line.set_xdata(xdata)
                track_line.set_ydata(ydata)
                track_text.set_position((bearing_as_radian, range))
        except Exception as x:
            print(F"Update track for {track_name} got exception {x}")

    def remove_track(self, track_name: str):
        try:
            track = self.tracks[track_name] if track_name in self.tracks else None
            if track is None:
                #print(F"Track {track_name} not found")
                return

            track_line = track['track_line']
            track['track_line'] = None
            self.ax.lines.remove(track_line)
            del track_line

            track_text = track['track_text']
            track_text.remove()
            track['track_text'] = None
            del track_text

            del self.tracks[track_name]
            #print(F"Removing {track_name} from radar")
        except Exception as x:
            print(f"Exception in remove track: {x}")

    def add_place(self, label, lat, lon):
        # compute heading and bearing from the site
        bearing, range = self.compute_bearing_vector(lat, lon)
        bearing_as_radian = np.radians(bearing)

        self.ax.plot(bearing_as_radian, range, "s")
        track_text = self.ax.text(bearing_as_radian, range, label, **text_style)


def update_track(track_name: str, lat, lon):

    if lat is None or lon is None:
        remove_track(track_name)
        return

    _radar1.update_track(track_name, lat, lon)
    _radar2.update_track(track_name, lat, lon)

    _radar1.refresh()
    _radar2.refresh()


def remove_track(track_name: str):
    _radar1.remove_track(track_name)
    _radar2.remove_track(track_name)
    _radar1.refresh()
    _radar2.refresh()


home_lat = 45.25056
home_lon = -75.89996

yow_lat = 45.320165386
yow_lon = -75.668163994


plt.ion()
fig = plt.figure(figsize=(12,5))  # size
plt.grid(color='#888888')

_radar1 = Radar(fig,121, home_lat, home_lon)
_radar2 = Radar(fig,122, yow_lat, yow_lon, 25)

_radar1.add_place('YOW', yow_lat, yow_lon)
_radar2.add_place('H', home_lat, home_lon)
_radar1.refresh()
_radar2.refresh()

