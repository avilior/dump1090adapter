import logging
from pathlib import Path
from asyncio.queues import Queue
from asyncio import CancelledError
from store.sbs1 import SBS1Message
from store.db_process_sbs1_msg2 import db_process_sbs1_msg
from databases import Database

from dump1090processor.dump1090receiver import INCOMING_ACTION_TYPE

LOG = logging.getLogger(__name__)


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


async def dbWorker(db_path: str, db_workerQ: Queue):

    LOG.info("Starting")
    if db_workerQ is None:
        LOG.info(F"db worker queue is None not starting ")
        return

    LOG.info(F"Connecting to db at url: {db_path}")

    try:
        database = Database(db_path)

        await database.connect()

        transaction = await database.transaction()

        await database.execute(CREATE_TRACK_POINT_TABLE)

        await transaction.commit()

        LOG.info("Connected and created table (if non existed")

    except Exception:
        LOG.exception("Exception while creating database")
        LOG.info("Exiting")
        return None

    while True:

        if not database.is_connected:
            LOG.info(F"@dbWorker: reconnecting to database...")
            await database.connect()
            LOG.info(F"@dbWorker: reconnecting to database. Done")

        try:
            while True:
                incoming_action:INCOMING_ACTION_TYPE = await db_workerQ.get()
                action_types = incoming_action.actionTypes
                icao_rec = incoming_action.actionMsg

                #print(F"DB_WORKER_RXED: {action_types} {icao_rec}")

                #await db_process_sbs1_msg2(database, sbs1_msg)
                await db_process_sbs1_msg(database, incoming_action.aircraftId, icao_rec['last_seen'], icao_rec['current'])

        except CancelledError:
            LOG.info("Cancelling")
            break
        except Exception as x:
            LOG.exception("General exception")
        finally:
            await database.disconnect()

    LOG.info("Exiting")
    return None