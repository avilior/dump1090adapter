from pathlib import Path
from store.sbs1 import SBS1Message
import aiosqlite
from databases import Database
from datetime import datetime
import logging

LOG = logging.getLogger(__name__)


CREATE_ICAO_TABLE = """CREATE TABLE IF NOT EXISTS icao (
                            icao text PRIMARY KEY,
                            first_seen text NOT NULL,
                            last_seen  text
                       );"""

# when i get a icao event i wnat to insert a row or update last seen


CREATE_TRACK_POINT_TABLE = """CREATE TABLE IF NOT EXISTS track_point(
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


async def create_connection(db_file: Path):
    try:
        conn = await aiosqlite.connect(str(db_file))

        return conn

    except aiosqlite.Error as x:
        LOG.exception("aiosqlite error.")
    except Exception as x:
        LOG.exception("general exception")

    return None

async def create_table(db_conn, create_table_sql):

    try:
        c = await db_conn.cursor()
        await c.execute(create_table_sql)
    except aiosqlite.Error as e:
        print(e)



async def upsert_point(database: Database, icao,ts, lat = None,lon = None, callsign = None, hd = None, altitude = None, gspd=None,vrt=None):

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
    q = F"UPDATE track_point SET\n {terms_string} {where}"
    #print(q)

    try:

        transaction = await database.transaction()

        #print("@upsert_point: transaction started")

        # we need the cursor to determine how many rows are inserted so we can do the upsert

        conn = database.connection().raw_connection

        c = await conn.cursor()

        await c.execute(q)

        if c.rowcount == 0:
            # do an insert
            insert_q = F'INSERT INTO track_point ({columns_string}) VALUES ({values_string})'
            await c.execute(insert_q)
            #print(F"Inserted {c.rowcount}")
        else:
            #print(F"Updated {c.rowcount}")
            pass

        # check if there are any changes

        await transaction.commit()

        #print("@upsert_point: transaction commited")

    except aiosqlite.Error as e:
        LOG.error(F"@upsert_point: Caught aiosqlite.Error: {e}")
        raise
    except Exception as x:
        LOG.error(F"@upsert_point: Caught exception {x}")
        raise

async def db_process_sbs1_msg(database, icao24: str, timestamp: datetime, rec: dict):

    #print("DB_PROCESS_SBS1_MSG")

    #msg.dump()
        # get the database record for the icao
    #print(F"Fetching database record for icao24")
    #                  (db_conn, icao,ts, lat = None,lon = None, callsign = None, hd = None, altitude = None, gspd=None,vrt=None):

    await upsert_point(database,
                       icao24,
                       timestamp,
                       lat=rec['lat'], lon=rec['lon'],
                       callsign=rec['callsign'],
                       hd=rec['track'],  # heading
                       altitude=rec['altitude'],
                       gspd=rec['groundSpeed'],
                       vrt=rec['verticalRate']
                       )

