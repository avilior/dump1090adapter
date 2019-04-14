from .sbs1 import SBS1Message
import texttable
import datetime
import os
from dump1090adapter.radar import update_track,  remove_track

from geographiclib.geodesic import Geodesic

import aiosqlite

db = {}   # icao24  {  lasts generatedDate }


def process4db(sbs1msg:SBS1Message):
    if not sbs1msg.isValid:
        return
    # if icao24 is not in database then create a record for it
    # if icao24 is in database then update last seen


def process(sbs1msg:SBS1Message):
    if not sbs1msg.isValid:
        print("Message not valid")
        return


    #sbs1msg.dump()
    # check to see if the icao24 is in the db
    if sbs1msg.icao24 not in db:

        #print(F"New aircraft {sbs1msg.icao24}")
        db[sbs1msg.icao24] = {
            'last_seen' : None,
            'current'   : {
                "callsign"         : None,
                "altitude"         : None,
                "groundSpeed"      : None,
                "track"            : None,
                "lat"              : None,
                "lon"              : None,
                "verticalRate"     : None,
                "squawk"           : None,
                "alert"            : None,
                "emergency"        : None,
                "spi"              : None,
                "onGround"         : None
                }
            }

    r = db[sbs1msg.icao24]
    c = r['current']

    r['last_seen'] = sbs1msg.loggedDate


    if sbs1msg.messageType == 'MSG':

        if sbs1msg.transmissionType == 1:

            c["callsign"]    = sbs1msg.callsign

        elif sbs1msg.transmissionType == 2:

            c["altitude"]    = sbs1msg.altitude
            c["groundSpeed"] = sbs1msg.groundSpeed
            c["track"]       = sbs1msg.track
            c["lat"]         = sbs1msg.lat
            c["lon"]         =  sbs1msg.lon
            c["onGround"]    = sbs1msg.onGround

        elif sbs1msg.transmissionType == 3:

            c["altitude"]    = sbs1msg.altitude
            c["lat"]         = sbs1msg.lat
            c["lon"]         = sbs1msg.lon
            c["alert"]       = sbs1msg.alert
            c["emergency"]   = sbs1msg.emergency
            c["spi"]         = sbs1msg.spi
            c["onGround"]    = sbs1msg.onGround

        elif sbs1msg.transmissionType == 4:

            c["groundSpeed"]  = sbs1msg.groundSpeed
            c["track"]        = sbs1msg.track
            c["verticalRate"] = sbs1msg.verticalRate

        elif sbs1msg.transmissionType == 5:

            c["altitude"]     = sbs1msg.altitude
            c["alert"]        = sbs1msg.alert
            c["spi"]          = sbs1msg.spi
            c["onGround"]     = sbs1msg.onGround

        elif sbs1msg.transmissionType == 6:

            c["altitude"]     = sbs1msg.altitude
            c["squawk" ]      = sbs1msg.squawk
            c["alert"]        = sbs1msg.alert
            c["emergency"]    = sbs1msg.emergency
            c["spi"]          = sbs1msg.spi
            c["onGround"]     = sbs1msg.onGround

        elif sbs1msg.transmissionType == 7:

            c["altitude"]     = sbs1msg.altitude
            c["onGround"]     = sbs1msg.onGround

        elif sbs1msg.transmissionType == 8:

            c["onGround"] = sbs1msg.onGround

        else:
            print("WTF????")
    else:
        print(F"Received {sbs1msg.messageType} msg")

    #print(f"{sbs1msg.icao24} {db[sbs1msg.icao24]}")

home_lat = 45.25056
home_lon = -75.89996

yow_lat = 45.320165386
yow_lon = -75.668163994


def dump_store():

    table = texttable.Texttable()

    table.header(["ICAO","CALLSIGN","SQUAWK","GROUND","LAT","LON","HD","ALT","V-RATE","LAND","YOW-D","YOW-HD","HOME-D","HOME-HD","AGE"])
    table.set_header_align(["l","l","l","l","l","l","l","l","l","l","l","l","l","l","l"])
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





