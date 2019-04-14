# dump1090 Adapter

# Functional Description

## Dump1090 Data Receiver

* Receives data from dump1090
    * Default port 3003
    * In my setup the host is host = "172.17.17.48"


# Design

* use [fastapi](https://github.com/tiangolo/fastapi) to provide:
    * runtime environment
    * restful api
    * websocket environment for the UI
    * database to store the received data
* use [uvicorn](https://www.uvicorn.org) to host the application.
* use [starlette](https://www.starlette.io)
    * fastapi is built ontop of starlette

# Implementation

## Application

* start uvicorn as part of the application

## Receiving data from dump1090

* data is sent over  TCP.
* use asyncio TCP Stream open_connection

## Monitor

* runs periodically : pass in the period in seconds
* prints the table using [texttable](https://github.com/foutaise/texttable/)
* compute heading distance using : geographiclib.geodesic
     * [inverse](https://geographiclib.sourceforge.io/html/python/code.html#geographiclib.geodesic.Geodesic.Inverse)

# ADSB / SBS1 Decoding

* source library [pyModeS](https://github.com/junzis/pyModeS)
* decoding  [SBS1](http://woodair.net/sbs/article/barebones42_socket_data.htm)


# WEBSITE

https://www.libhomeradar.org/airlines/N9/NVR/Novair.html?qid=0&page=22
https://www.planespotters.net/hex/ADD691
https://flightaware.com/live/flight/N991CE

# Improvements:
## What to store:

### ICAO24

* This represents the plane
* When seeing this check current db and if not found fetch the record from the internet
* Record the first time we see it and the last time we see it
* Each time we see the ICA024 and a Callsign then recored the Callsign against the ICAO24

### A Track

* icao24 <callsign> first_time last_time  -- unique_id(icao24|ts)
* unigue_id ts, lat lon hd altitude v-rate ground speed
* Record the paths of the flight each point should include the timestamp
* Record the ICAO24 of the path
* Record the callsign
    * if the callsign is associated with a FLIGHT like AC0303 then we can save the FLIGHT info
        * from
        * to

* what happens if a plane (icao24) comes in range, leaves range and comes back.  Is that a different track?
    * this can also be a plane landing and taking off
