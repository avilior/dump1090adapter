
import asyncio
from pathlib import Path
from fastapi import FastAPI
import os
import uvicorn

from dump1090TCPListener import dump1090TCPListener
from dump1090processor.dump1090receiver import dump1090Receiver
from monitor import monitor_worker
import monitor
from store.db_worker import dbWorker, connectingDB
#from radar import radar
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from websocket_broadcaster import websocketBroadcaster

import logging

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '80'))
DB_URL = os.getenv('DBURL','sqlite://localhost/../database/dump1090db.sqlite')
PUBLIC_PATH = os.getenv('PUBLIC', "../public")
DUMPHOST = os.getenv("DUMPHOST",None)
DUMPPORT = int(os.getenv("DUMPORT", "30003"))


#CREATE_DB = True     # always create the db files
#BASE_DIR = Path(__file__).resolve().parent
#db_file = BASE_DIR.parent / Path("database/") / Path("dump1090.sqlite")
#DB_URL = 'sqlite:///Users/avi/developer/python/dump1090adapter/database/dump1090db.sqlite'
#DB_URL = 'sqlite:///../database/dump1090db.sqlite'


tasks = []

LOG = logging.getLogger("app")
LOG.setLevel(logging.DEBUG)

app = FastAPI()

app.mount("/app", StaticFiles(directory=PUBLIC_PATH), name='public')

# weird sometime needed sometime not????
app.mount("/static", StaticFiles(directory=PUBLIC_PATH+"/static/",check_dir=False), name='static')


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:3000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>

@app.get("/")
async def read_root():
    return HTMLResponse(html)
"""

@app.get("/stats")
async def get_stats():
    x = monitor.get_stats()
    return x


websocket_clients = {}

@app.websocket_route("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    netloc = F"{websocket.client.host}:{websocket.client.port}"
    LOG.info(F"Connected client {netloc}")
    websocket_clients[netloc] = {"ws": websocket}

    try:
        #TODO send the current state to the new client
        while True:
            #print(F"{websocket.state} {websocket.application_state}")
            data = await websocket.receive_text()
            #await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect as wsx:
        LOG.info(F"Websocket disconnected: {netloc}")
    finally:
        LOG.info(F"Websocket closing: {netloc}")
        await websocket.close()
        del websocket_clients[netloc]


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.on_event('startup')
async def startup():
    LOG.info("Startup: starting")

    if DUMPHOST is None:
        LOG.error(F"dump1090 Host must be provided.")
        return None

    dumpPeriod   = 60 # number of seconds between dumps.  -1 means dont dump
    # this is called in the context of starlette before the main loop starts to execute.

    loop = asyncio.get_event_loop()

    dump1090IncomingQueue = asyncio.queues.Queue()
    db_worker_queue       = asyncio.queues.Queue() # used to send the db_worker messages to work on.
    radar_queue           = asyncio.queues.Queue() # used to send the radar task messages to display
    websocket_queue       = asyncio.queues.Queue() # use to send data to the websocket broadcaster

    #db_worker_queue = None  # disable database inserts
    radar_queue = None

    try:

        db_connection = await connectingDB(DB_URL)
        if db_connection:
            dbWorkerTask = loop.create_task(dbWorker(db_connection, db_worker_queue))
            tasks.append(dbWorkerTask)
        else:
            LOG.info("Database is not available")
            db_worker_queue = None

        #radarTask = loop.create_task(radar(radar_queue))
        #tasks.append(radarTask)

        dump1090TCPListenerTask = loop.create_task(dump1090TCPListener(dump1090IncomingQueue, DUMPHOST, DUMPPORT))
        tasks.append(dump1090TCPListenerTask)

        dump1090receiverTask = loop.create_task(dump1090Receiver(dump1090IncomingQueue, db_worker_queue, radar_queue, websocket_queue))
        tasks.append(dump1090receiverTask)

        if dumpPeriod > -1:
            monitorTask = loop.create_task(monitor_worker(dumpPeriod))
            tasks.append(monitorTask)

        websocketBroadcasterTask = loop.create_task(websocketBroadcaster(websocket_clients, websocket_queue))
        tasks.append(websocketBroadcasterTask)
    except Exception as x:
        LOG.exception(F"Startup: Exception {x}")

    LOG.info('startup: finishing')

@app.on_event('shutdown')
async def shutdown():
    LOG.info("Shuting down")

    for task in tasks:
        LOG.debug("shuting down a task")
        if not task.cancelled():
            task.cancel()

if __name__ == "__main__":

    env_string = F"HOST={HOST}\nPORT={PORT}\nDB_URL={DB_URL}\nPUBLIC_PATH={PUBLIC_PATH}\nDUMPHOST={DUMPHOST}\nDUMPPORT={DUMPPORT}"

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d|%(name)-12s|%(levelname)-8s| %(message)s',
                        datefmt='%m-%d %H:%M:%S')

    LOG.info(F"Environmnet Vars:\n{env_string}")

    uvicorn.run(app, host=HOST, port=PORT)