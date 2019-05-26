import asyncio
#from store.store import dump_store

from dump1090TCPListener import STATS
#import radar
import traceback

import logging

LOG = logging.getLogger(__name__)

def get_stats():
    #return {'radar': radar.get_stats(), 'dump1090TCPListener': STATS}
    return {'dump1090TCPListener': STATS}

async def monitor_worker(period: int):
    LOG.info("Starting")
    while True:
        try:
            await asyncio.sleep(period)

            #dump_store()
            LOG.info("=======================================================================================================================")
            LOG.info(F"dump1090TCPListener: {STATS}")
            #print(F"radar              : {radar.get_stats()}")
            LOG.info("=======================================================================================================================")
            STATS["max_incomingQ_size"]=0
            #radar.reset_stats()
        except asyncio.CancelledError:
            print("Canceled dump period")
            break
        except Exception:
            LOG.exception("General exception.")

    LOG.info("Exiting")
