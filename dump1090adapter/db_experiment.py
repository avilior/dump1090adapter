import sqlite3
from sqlite3 import Error
from pathlib import Path
import sys

CREATE_DB = True

CREATE_ICAO_TABLE = """CREATE TABLE IF NOT EXISTS icao (
                            icao text PRIMARY KEY,
                            first_seen text NOT NULL,
                            last_seen  text
                       );"""

# when i get a icao event i wnat to insert a row or update last seen


CREATE_POINT_TABLE = """CREATE TABLE IF NOT EXISTS point(
                            icao text,
                            ts text,   
                            callsign text,
                            lat real,
                            lon real,
                            hd real,
                            altitude integer, 
                            gspd integer,
                            vrt integer,
                            PRIMARY KEY (icao, ts)
                        );"""


BASE_DIR = Path(__file__).resolve().parent


db_file = BASE_DIR.parent / Path("database/") / Path("dump1090sqlite3.db")

def update_icao(db_con, icao, seen_date):
    INSERT_OR_UPDATE_ICAO = F"""INSERT INTO icao (icao,first_seen, last_seen) VALUES ("{icao}","{seen_date}","{seen_date}")
                                ON CONFLICT(icao) 
                                DO UPDATE SET last_seen=excluded.last_seen;"""

    print(INSERT_OR_UPDATE_ICAO)
    try:
        c = db_con.cursor()
        c.execute(INSERT_OR_UPDATE_ICAO)
        db_con.commit()
    except Error as e:
        print(e)

def upsert_point(db_con, icao,ts, lat = None,lon = None, callsign = None, hd = None, altitude = None, gspd=None,vrt=None):

    terms = []
    columns = []
    values  = []
    if icao:
        columns.append('icao')
        values.append(f'"{icao}"')
    if ts:
        columns.append('ts')
        values.append(f'"{ts}"')
    if lat:
        terms.append(F'lat={lat}')
        columns.append('lat')
        values.append(f'{lat}')
    if lon:
        terms.append(F'lon={lon}')
        columns.append('lon')
        values.append(f'{lon}')
    if callsign:
        terms.append(F'callsign="{callsign}"')
        columns.append('callsign')
        values.append(f'"{callsign}"')
    if hd:
        terms.append(F'hd={hd}')
        columns.append('hd')
        values.append(f'{hd}')
    if altitude:
        terms.append(F'altitude={altitude}')
        columns.append('altitude')
        values.append(f'{altitude}')
    if gspd:
        terms.append(F'gspd={gspd}')
        columns.append('gspd')
        values.append(f'{gspd}')
    if vrt:
        terms.append(F'vrt={vrt}')
        columns.append('vrt')
        values.append(f'{vrt}')

    if len(terms) == 0:
        return

    terms_string = ',\n'.join(terms)
    columns_string = ','.join(columns)
    values_string  = ','.join(values)

    where = F'WHERE icao = "{icao}" AND ts = "{ts}";'
    q = F"UPDATE point SET\n {terms_string} {where}"
    print(q)

    try:
        c = db_con.cursor()
        c.execute(q)

        if c.rowcount == 0:
            # do an insert
            insert_q = F'INSERT INTO point ({columns_string}) VALUES ({values_string})'
            c.execute(insert_q)
            print(F"Inserted {c.rowcount}")
        else:
            print(F"Updated {c.rowcount}")

        # check if there are any changes

        db_con.commit()
    except Error as e:
        print(e)


def insert_pointx(db_con, icao,ts, lat = None,lon = None, callsign = None, hd = None, altitude = None, gspd=None,vrt=None):
    INSERT_POINT=F"""INSERT INTO point (icao,ts, callsign, lat,lon, ,hd, altitude,gspd,vrt) VALUES ("{icao}", "{ts}", {callsign}, {lat}, {lon}, {hd}, {altitude}, {gspd}, {vrt})
                     ON CONFLICT (icao, ts)
                     DO UPDATE SET callsign=excluded.callsign, lat = excluded.lat, lon=excluded.lon, hd=excluded.hd, altitude=excluded.altitude, gspd=excluded.gspd, vrt=excluded.vrt"""

    print(INSERT_POINT)
    try:
        c = db_con.cursor()
        c.execute(INSERT_POINT)
        db_con.commit()
    except Error as e:
        print(e)

def create_connection(db_file: Path):
    try:
        db_con = sqlite3.connect(str(db_file))
        print(sqlite3.version)

        return db_con

    except Error as x:
        print(x)
    except Exception as x:
        print(x)

    return None

def create_table(db_con, create_table_sql):

    try:
        c = db_con.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def main():
    if not db_file.exists() and not CREATE_DB:
        print("Database does not exist.  To create it set CREATE_DB to True")
        return

    db_con = create_connection(str(db_file))

    if db_con:
        create_table(db_con, CREATE_ICAO_TABLE)
        create_table(db_con, CREATE_POINT_TABLE)

    update_icao(db_con, "XYZ", "NOW")

    icao = "DEAD"
    ts = '2019-04-14 02:57:28.205096'

    upsert_point(db_con, icao, ts,lat = 45, lon = -75, callsign = "zzz")
    upsert_point(db_con, icao, ts, altitude=35000)
    upsert_point(db_con, icao, ts, gspd=510)
    upsert_point(db_con, icao, ts, vrt=-1200)




    db_con.close()


if __name__ == "__main__":
    main()