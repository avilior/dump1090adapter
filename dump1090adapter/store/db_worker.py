import logging
from asyncio.queues import Queue
from asyncio import CancelledError
from dump1090adapter.store.sbs1 import SBS1Message
from dump1090adapter.store.db_process_sbs1_msg import db_process_sbs1_msg

LOG = logging.getLogger("dump1090Receiver")


async def dbWorker(db_workerQ: Queue):
    while True:
        try:
            while True:
                sbs1_msg = await db_workerQ.get()

                db_process_sbs1_msg(sbs1_msg)


        except CancelledError:
            break
        except Exception as x:
            print(F"Exception {x}")
        finally:
            pass