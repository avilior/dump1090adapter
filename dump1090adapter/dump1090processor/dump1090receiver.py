import logging
from asyncio.queues import Queue
from asyncio import CancelledError
from dump1090adapter.store.sbs1 import SBS1Message
from dump1090adapter.store.store import process, process4db

LOG = logging.getLogger("dump1090Receiver")


async def dump1090Receiver(incomingQ: Queue, db_worker_Q: Queue):
    try:
        while True:
            raw_sbs1_msg = await incomingQ.get()
            #print(f"{raw_item}")

            sbs1_msg = SBS1Message(raw_sbs1_msg)
            if sbs1_msg.isValid:
                db_worker_Q.put_nowait(sbs1_msg)
                process(sbs1_msg)
            else:
                print("WARN: Invalid sbs1_msg. Failed processing")

    except CancelledError:
        pass
    except Exception as x:
        print(F"Exception {x}")
    finally:
        pass