from pathlib import Path
from dump1090adapter.store.sbs1 import SBS1Message
import aiosqlite


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
        print(x)
    except Exception as x:
        print(x)

    return None

async def create_table(db_conn, create_table_sql):

    try:
        c = await db_conn.cursor()
        await c.execute(create_table_sql)
    except aiosqlite.Error as e:
        print(e)


async def prepare_db(db_file: Path, create_flag = False):

    if not db_file.exists() and not create_flag:
        print("Database does not exist.  To create it set CREATE_DB to True")
        return

    async with aiosqlite.connect(str(db_file)) as db:
        await db.execute(CREATE_TRACK_POINT_TABLE)
        await db.commit()


    """
    db_conn = await create_connection(db_file)

    if db_conn:
        await create_table(db_conn, CREATE_ICAO_TABLE)
        await create_table(db_conn, CREATE_TRACK_POINT_TABLE)
        await db_conn.commit()
        await db_conn.close()
    """

async def upsert_point(db_conn, icao,ts, lat = None,lon = None, callsign = None, hd = None, altitude = None, gspd=None,vrt=None):

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
        c = await db_conn.cursor()
        await c.execute(q)

        if c.rowcount == 0:
            # do an insert
            insert_q = F'INSERT INTO point ({columns_string}) VALUES ({values_string})'
            await c.execute(insert_q)
            print(F"Inserted {c.rowcount}")
        else:
            print(F"Updated {c.rowcount}")

        # check if there are any changes

        await db_conn.commit()
    except aiosqlite.Error as e:
        print(e)

async def db_process_sbs1_msg(db_conn, msg: SBS1Message):

    #msg.dump()
    #print(msg.icao24)
    #print(msg.generatedDate)

    # get the database record for the icao
    #print(F"Fetching database record for icao24")
    #                  (db_conn, icao,ts, lat = None,lon = None, callsign = None, hd = None, altitude = None, gspd=None,vrt=None):
    await upsert_point(db_conn,msg.icao24,
                       msg.generatedDate,
                       lat=msg.lat, lon=msg.lon,
                       callsign=msg.callsign,
                       hd=msg.track,  # heading
                       altitude=msg.altitude,
                       gspd=msg.groundSpeed,
                       vrt=msg.verticalRate
                       )
