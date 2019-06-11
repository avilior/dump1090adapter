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


### fastAPI and database

https://fastapi.tiangolo.com/tutorial/async-sql-databases/

https://github.com/encode/databases

# Docker

Added environment variable so these have to be specified 
```bash
ARG BIND_HOST=0.0.0.0
ARG LISTEN_PORT=80

ENV PYTHONBUFFERED=1
ENV HOST=$BIND_HOST
ENV PORT=$LISTEN_PORT

ENV DB_URL=sqlite://localhost/../database/dump1090db.sqlite
ENV PUBLIC_PATH=../public
ENV DUMPHOST=0.0.0.0
ENV DUMPPORT=30003

```


```
docker build -t dump1090rx .
```

```
docker run -it --rm -p4000:4000 dump1090rx bash
```

```
 docker run -it -p 4000:4000 -v $PWD/public/:/public/ --name dump1090rx dump1090rx bash
 ```

# Issues

## cant reach inside a container to outside mac - Host not reachable

Need to enable ip packet forwarding

```
MBP2014:~ avi$ sysctl -a net.inet.ip.forwarding
net.inet.ip.forwarding: 0
MBP2014:~ avi$ sudo sysctl -w net.inet.ip.forwarding=1
Password:
net.inet.ip.forwarding: 0 -> 1
```

How do i enable perm? Should I enable perm?  What about linux?

To get this going:
```
docker run -it ubuntu bash

Then inside the container we need to install ping

# apt-get update

# apt-get install -y iputils-ping

```

On ubuntu this is working fine on MAC i have an issue
Note on my unbuntu machine forwarding is enabled
sudo sysctl -a | grep forwarding
net.ipv4.conf.all.forwarding = 1

