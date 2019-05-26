from .sbs1 import SBS1Message
import texttable
import datetime
from collections import namedtuple
#from dump1090adapter.radar import update_track,  remove_track

from geographiclib.geodesic import Geodesic

import logging

LOG = logging.getLogger(__name__)

import aiosqlite

SBS1Changed = namedtuple('SBS1Changed', ['id',
                                         'new_aircraft',
                                         'callsign',
                                         'squawk',
                                         'altitude',
                                         'ground_speed',
                                         'track',
                                         'lat',
                                         'lon',
                                         'vertical_rate',
                                         'on_ground',
                                         'alert',
                                         'emergency',
                                         'spi',
                                         'icao_record'
                                         ])

# local store of aircraft that we are currently monitoring
db2 = {}

last_flush_time = datetime.datetime.utcnow()

def flush_cache(seconds):
    global last_flush_time

    time_now = datetime.datetime.utcnow()

    if (time_now - last_flush_time).total_seconds() < 60:
        return

    last_flush_time = time_now

    items_to_remove = []
    max_delta = 0
    for id,r in db2.items():
        delta_sec = (time_now - r['last_seen']).total_seconds()
        max_delta = max(max_delta, delta_sec)
        if delta_sec > 300:
                items_to_remove.append(id)
    LOG.info(F"FLUSH: length of cache {len(db2)} Items to remove {len(items_to_remove)} max: {max_delta}")
    for id in items_to_remove:
        del db2[id]

def update(c, field_name, value):
    if value != None:
        changed = c[field_name] != value
        c[field_name] = value
        return changed
    return False

def process2(sbs1msg:SBS1Message):

    if not sbs1msg.isValid:
        print("Message not valid")
        return

    new_aircraft         = False
    changed_callsign     = False
    changed_squawk       = False
    changed_altitude     = False
    changed_ground_speed = False
    changed_track        = False
    changed_lat          = False
    changed_lon          = False
    changed_vertical_rate= False
    changed_on_ground    = False
    changed_alert        = False
    changed_emergency    = False
    changed_spi          = False

    if sbs1msg.icao24 not in db2:
        db2[sbs1msg.icao24] = {
            'last_seen': None,
            'current': {
                "callsign":    None,
                "altitude":    None,
                "groundSpeed": None,
                "track":       None,
                "lat":         None,
                "lon":         None,
                "verticalRate":None,
                "squawk":      None,
                "alert":       None,
                "emergency":   None,
                "spi":         None,
                "onGround":    None
            }
        }
        new_aircraft = True

    r = db2[sbs1msg.icao24]
    c = r['current']

    r['last_seen'] = sbs1msg.loggedDate

    if sbs1msg.messageType == 'MSG':

        if sbs1msg.transmissionType == 1:

            changed_callsign = update(c, "callsign", sbs1msg.callsign)

        elif sbs1msg.transmissionType == 2:

            changed_altitude     = update(c, "altitude",    sbs1msg.altitude)
            changed_ground_speed = update(c, "groundSpeed", sbs1msg.groundSpeed)
            changed_track        = update(c, "track",       sbs1msg.track)
            changed_lat          = update(c, "lat",         sbs1msg.lat)
            changed_lon          = update(c, "lon",         sbs1msg.lon)
            changed_on_ground    = update(c, "onGround",    sbs1msg.onGround)

        elif sbs1msg.transmissionType == 3:

            changed_altitude = update(c, "altitude",  sbs1msg.altitude)
            changed_lat      = update(c, "lat",       sbs1msg.lat)
            changed_lon      = update(c, "lon",       sbs1msg.lon)
            changed_alert    = update(c, "alert",     sbs1msg.alert)
            changed_emergency= update(c, "emergency", sbs1msg.emergency)
            changed_spi      = update(c, "spi",       sbs1msg.spi)
            changed_on_ground= update(c, "onGround",  sbs1msg.onGround)

        elif sbs1msg.transmissionType == 4:

            changed_ground_speed  = update(c, "groundSpeed",  sbs1msg.groundSpeed)
            changed_track         = update(c, "track",        sbs1msg.track)
            changed_vertical_rate = update(c, "verticalRate", sbs1msg.verticalRate)

        elif sbs1msg.transmissionType == 5:

            changed_altitude = update(c, "altitude", sbs1msg.altitude)
            changed_alert    = update(c, "alert",    sbs1msg.alert)
            changed_spi      = update(c, "spi",      sbs1msg.spi)
            changed_on_ground= update(c, "onGround", sbs1msg.onGround)

        elif sbs1msg.transmissionType == 6:

            changed_altitude = update(c, "altitude",  sbs1msg.altitude)
            changed_squawk   = update(c, "squawk",    sbs1msg.squawk)
            changed_alert    = update(c, "alert",     sbs1msg.alert)
            changed_emergency= update(c, "emergency", sbs1msg.emergency)
            changed_spi      = update(c, "spi",       sbs1msg.spi)
            changed_on_ground = update(c, "onGround",  sbs1msg.onGround)

        elif sbs1msg.transmissionType == 7:

            changed_altitude  = update(c, "altitude", sbs1msg.altitude)
            changed_on_ground = update(c, "onGround", sbs1msg.onGround)

        elif sbs1msg.transmissionType == 8:

            changed_on_ground = update(c, "onGround", sbs1msg.onGround)

        else:
            print("WTF????")
            return
    else:
        print(F"Received un handled message type: {sbs1msg.messageType}")
        return

    return SBS1Changed(
                id           = sbs1msg.icao24,
                new_aircraft = new_aircraft,
                callsign     = changed_callsign,
                squawk       = changed_squawk,
                altitude     = changed_altitude,
                ground_speed = changed_ground_speed,
                track        = changed_track,
                lat          = changed_lat,
                lon          = changed_lon,
                vertical_rate= changed_vertical_rate,
                on_ground    = changed_on_ground,
                alert        = changed_alert,
                emergency    = changed_emergency,
                spi          = changed_spi,
                icao_record= r)


home_lat = 45.25056
home_lon = -75.89996

yow_lat = 45.320165386
yow_lon = -75.668163994


TABLE_COL_NAME  = ["ICAO","CALLSIGN","SQUAWK","GROUND","LAT","LON","HD","ALT","V-RATE","LAND","YOW-D","YOW-HD","HOME-D","HOME-HD","AGE"]
TABLE_ALIGNMENT = ["l","l","l","l","l","l","l","l","l","l","l","l","l","l","l"]

def dump_row(db, icao24):
    table = texttable.Texttable()

    table.header(TABLE_COL_NAME)
    table.set_header_align(TABLE_ALIGNMENT)
    table.set_max_width(0)

    r = db[icao24]
    if r is None:
        return

    c = r['current']

    delta_sec = (datetime.datetime.utcnow() - r['last_seen']).total_seconds()

    yow_distance = '-'
    yow_heading = '-'
    home_distance = '-'
    home_heading = '-'
    if c['lat'] is not None and c['lon'] is not None:
        yow = Geodesic.WGS84.Inverse(yow_lat, yow_lon, c['lat'], c['lon'])
        yow_distance = yow['s12'] / 1e3
        yow_heading = yow['azi1']

        home = Geodesic.WGS84.Inverse(home_lat, home_lon, c['lat'], c['lon'])
        home_distance = home['s12'] / 1e3
        home_heading = home['azi1']
        if home_heading < 0:
            home_heading = 360 + home_heading
        if yow_heading < 0:
            yow_heading = 360 - yow_heading

    # CLASS A Airspace Flight Level conversion
    if c['altitude'] is not None and c['altitude'] > 18000:
        altitude = F"FL{int(c['altitude'] / 100):03d}"
    else:
        altitude = c['altitude']


    row = [icao24, c['callsign'], c["squawk"], c["groundSpeed"], c['lat'], c['lon'], c["track"], altitude, c["verticalRate"], c["onGround"], yow_distance, yow_heading, home_distance, home_heading, delta_sec]

    table.add_row(row)

    print(f"{table.draw()}")

"""
def dump_store():

    table = texttable.Texttable()

    table.header(TABLE_COL_NAME)
    table.set_header_align(TABLE_ALIGNMENT)
    table.set_max_width(0)

    time_now = datetime.datetime.utcnow()

    changed = False
    for icao24, r in db.items():
        c = r['current']

        delta_sec = (time_now - r['last_seen']).total_seconds()

        # if its really old ignore it -- we should really purge
        if delta_sec > 300.0:
            continue
        # if its begging to age delete it
        if delta_sec > 100.0:
            remove_track(icao24)
            continue
        # if it doesnt have lat lon then delete it from mapping and dont display it
        if c['lat'] is None or c['lon'] is None:
            remove_track(icao24)
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

        if c['lat'] is not None and c['lon'] is not None:
            update_track(icao24, c['lat'], c['lon'])

    if changed:
        print(F"{time_now}")
        print(f"{table.draw()}")

"""



