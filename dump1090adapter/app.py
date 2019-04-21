import asyncio
from pathlib import Path
from fastapi import FastAPI
import uvicorn
from dump1090adapter.dump1090TCPListener import dump1090TCPListener
from dump1090adapter.dump1090processor.dump1090receiver import dump1090Receiver
from dump1090adapter.monitor import monitor
from dump1090adapter.store.db_worker import dbWorker
from dump1090adapter.radar import radar



#CREATE_DB = True     # always create the db files
#BASE_DIR = Path(__file__).resolve().parent
#db_file = BASE_DIR.parent / Path("database/") / Path("dump1090.sqlite")
#DB_URL = 'sqlite:///Users/avi/developer/python/dump1090adapter/database/dump1090db.sqlite'
#DB_URL = 'sqlite:///../database/dump1090db.sqlite'
DB_URL = 'sqlite://localhost/../database/dump1090db.sqlite'

tasks = []

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World V3"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.on_event('startup')
async def startup():
    print('startup: starting')

    dump1090host = "172.17.17.48"
    dump1090port = 30003
    dumpPeriod   = -1 # number of seconds between dumps.  -1 means dont dump
    # this is called in the context of starlette before the main loop starts to execute.

    loop = asyncio.get_event_loop()

    dump1090IncomingQueue = asyncio.queues.Queue()
    db_worker_queue       = asyncio.queues.Queue() # used to send the db_worker messages to work on.
    radar_queue           = asyncio.queues.Queue() # used to send the radar task messages to display

    dbWorkerTask = loop.create_task(dbWorker(DB_URL, db_worker_queue))
    tasks.append(dbWorkerTask)

    radarTask = loop.create_task(radar(radar_queue))
    tasks.append(radarTask)

    dump1090TCPListenerTask = loop.create_task(dump1090TCPListener(dump1090IncomingQueue, dump1090host, dump1090port))
    tasks.append(dump1090TCPListenerTask)

    # db_worker_queue = None  # disable database inserts
    #radar_queue     = None
    dump1090receiverTask = loop.create_task(dump1090Receiver(dump1090IncomingQueue, db_worker_queue, radar_queue))
    tasks.append(dump1090receiverTask)

    if dumpPeriod > -1:
        monitorTask = loop.create_task(monitor(dumpPeriod))
        tasks.append(monitorTask)

    print('startup: finishing')

@app.on_event('shutdown')
async def shutdown():
    print("Shuting down")

    for task in tasks:
        print("shuting down a task")
        if not task.cancelled():
            task.cancel()

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")