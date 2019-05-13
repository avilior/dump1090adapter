import asyncio
#from store.store import dump_store

from dump1090TCPListener import STATS
import radar
import traceback

def get_stats():
    return {'radar': radar.get_stats(), 'dump1090TCPListener': STATS}

async def monitor_worker(period: int):
    print("Monitor Starting")
    while True:
        try:
            await asyncio.sleep(period)

            #dump_store()
            print("=======================================================================================================================")
            print(F"dump1090TCPListener: {STATS}")
            print(F"radar              : {radar.get_stats()}")
            print("=======================================================================================================================")
            STATS["max_incomingQ_size"]=0
            radar.reset_stats()
        except asyncio.CancelledError:
            print("Canceled dump period")
            break
        except Exception:
            traceback.print_exc()
