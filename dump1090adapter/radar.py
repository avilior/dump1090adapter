from asyncio.queues import Queue
from asyncio import CancelledError
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import texttable
import async_timeout

from geographiclib.geodesic import Geodesic

from dump1090processor.dump1090receiver import INCOMING_ACTION_TYPE

text_style = dict(horizontalalignment='center', verticalalignment='center', fontsize=8, fontdict={'family':'monospace'})

STATS = {
   'number_rx' : 0,
   'max_incoming_q_size': 0,
   'rx_expired': 0,
   'max_history_size': 0,
   'updates': 0
}

def get_stats():
    return STATS

def reset_stats():
    STATS['max_incoming_q_size'] = 0
    STATS['max_history_size'] = 0

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

home_lat = 45.25056
home_lon = -75.89996

yow_lat = 45.320165386
yow_lon = -75.668163994

plt.ion()
fig = plt.figure(figsize=(12, 5))  # size
plt.grid(color='#888888')

_radar1 = Radar(fig, 121, home_lat, home_lon)
_radar2 = Radar(fig, 122, yow_lat, yow_lon, 25)

_radar1.add_place('YOW', yow_lat, yow_lon)
_radar2.add_place('H', home_lat, home_lon)
_radar1.refresh()
_radar2.refresh()


def update_track(track_name: str, lat, lon):
    if lat is None or lon is None:
        remove_track(track_name)
        return

    _radar1.update_track(track_name, lat, lon)
    _radar2.update_track(track_name, lat, lon)

    #_radar1.refresh()
    #_radar2.refresh()

def refresh():
    _radar1.refresh()
    _radar2.refresh()


def remove_track(track_name: str):
    _radar1.remove_track(track_name)
    _radar2.remove_track(track_name)
    #_radar1.refresh()
    #_radar2.refresh()


history = {}
last_flush_time = datetime.utcnow()
def flush():
    global last_flush_time
    time_now = datetime.utcnow()
    if (time_now - last_flush_time).total_seconds() < 10:
        return
    last_flush_time = time_now

    ids_to_delete = []
    max_delta = 0
    for id, last_seen in history.items():
        delta_sec = (time_now - last_seen).total_seconds()
        max_delta = max(max_delta, delta_sec)
        if delta_sec > 300:
            remove_track(id)
            ids_to_delete.append(id)

    for id in ids_to_delete:
        del history[id]

    """
    print(F"Length of history: {len(history)} max delta: {max_delta}")
    for id, last_seen in history.items():
        print(F"{id} {int((time_now - last_seen).total_seconds())} | ", end='')
    print()
    """

TABLE_COL_NAME  = ["ICAO","CALLSIGN","SQUAWK","GROUND","LAT","LON","HD","ALT","V-RATE","LAND","YOW-D","YOW-HD","HOME-D","HOME-HD","AGE"]
TABLE_ALIGNMENT = ["l","l","l","l","l","l","l","l","l","l","l","l","l","l","l"]

table_store = {}

def update_table_store(id, last_seen, data):

    if id not in table_store:
        table_store[id] = {
            'last_seen': None,
            'current': {
                "callsign": None,
                "altitude": None,
                "groundSpeed": None,
                "track": None,
                "lat": None,
                "lon": None,
                "verticalRate": None,
                "squawk": None,
                "alert": None,
                "emergency": None,
                "spi": None,
                "onGround": None
            }
        }
    table_store[id]['last_seen'] = last_seen
    c = table_store[id]['current']
    merged = {**c,**data}
    table_store[id]['current'] = merged

last_table_render_time = datetime.utcnow()
def render_table_store():
    global last_table_render_time

    time_now = datetime.utcnow()

    if (time_now - last_table_render_time).total_seconds() < 10:
        return
    last_table_render_time = time_now

    table = texttable.Texttable()

    table.header(TABLE_COL_NAME)
    table.set_header_align(TABLE_ALIGNMENT)
    table.set_max_width(0)

    changed = False
    for icao24, r in table_store.items():
        c = r['current']

        delta_sec = (time_now - r['last_seen']).total_seconds()

        # if its really old ignore it -- we should really purge
        if delta_sec > 300.0:
            continue
        # if its begging to age delete it
        if delta_sec > 100.0:
            continue
        # if it doesnt have lat lon then delete it from mapping and dont display it
        if c['lat'] is None or c['lon'] is None:
            #remove_track(icao24)
            continue

        yow_distance  = '-'
        yow_heading   = '-'
        home_distance = '-'
        home_heading  = '-'
        if c['lat'] is not None and c['lon'] is not None:
            yow = Geodesic.WGS84.Inverse(yow_lat, yow_lon, c['lat'], c['lon'])
            yow_distance =  yow['s12'] / 1e3
            yow_heading  =  yow['azi1']

            home = Geodesic.WGS84.Inverse(home_lat, home_lon, c['lat'], c['lon'])
            home_distance = home['s12'] / 1e3
            home_heading  = home['azi1']
            if home_heading < 0:
                home_heading = 360 + home_heading
            if yow_heading < 0:
                yow_heading = 360 - yow_heading

        # convertions
        if c['altitude'] > 18000:
            altitude = F"FL{int(c['altitude']/100):03d}"
        else:
            altitude = c['altitude']
        row = [icao24,c['callsign'],c["squawk" ],c["groundSpeed"],c['lat'],c['lon'],c["track"],altitude,c["verticalRate"],c["onGround"], yow_distance,yow_heading, home_distance, home_heading, delta_sec]

        table.add_row(row)

        changed = True

    if changed:
        print(F"{time_now}")
        print(f"{table.draw()}")

async def radar(radar_Q: Queue = None):

    if radar_Q is None:
        print("Radar task is terminating. The radar_Q is None. Nothing to do")
        return

    try:
        q = Queue()

        while True:

            async with async_timeout.timeout(5) as tm:
                while True:
                    try:
                        incoming_action:INCOMING_ACTION_TYPE = await radar_Q.get()
                        q.put_nowait(incoming_action)
                        STATS['number_rx'] += 1
                        STATS['max_incoming_q_size'] = max(radar_Q.qsize(), STATS['max_incoming_q_size'])
                    except Exception as x:
                        break

            if not tm.expired:
                continue

            time_now = datetime.utcnow()

            while not q.empty():

                item = q.get_nowait()

                icao_rec = item.actionMsg

                # print(F"DB_WORKER_RXED: {action_types} {icao_rec}")

                # await db_process_sbs1_msg2(database, sbs1_msg)
                id = item.aircraftId
                last_seen = icao_rec['last_seen']
                data  = icao_rec['current']

                delta_sec = (time_now - last_seen).total_seconds()
                if delta_sec > 300:
                    print(F"@Radar: Got an old one: {id} {last_seen} {delta_sec}")
                    STATS['rx_expired'] += 1
                    remove_track(id)
                    del history[id]
                    continue

                history[id] = last_seen

                STATS['max_history_size'] = max(STATS['max_history_size'],len(history))

                if data['lon'] is not None and data['lat'] is not None:
                    update_track(id,data['lat'], data['lon'])
                    STATS['updates'] += 1

                update_table_store(id, last_seen, data)
                render_table_store()
            # endwhile

            # cleanup any lingering tracks:
            flush()

            refresh()


    except CancelledError:
            print("Cancellling radar task")

    except Exception as x:
        print(F"Exception {x}")





