import asyncio
from fastapi import FastAPI
import uvicorn
from dump1090adapter.dump1090TCPListener import dump1090TCPListener
from dump1090adapter.dump1090processor.dump1090receiver import dump1090Receiver
from dump1090adapter.monitor import monitor
from dump1090adapter.store.db_worker import dbWorker

tasks = []


app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello": "World V2"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

@app.on_event('startup')
async def startup():
    dump1090host = "172.17.17.48"
    dump1090port = 30003
    # this is called in the context of starlette before the main loop starts to execute.
    loop = asyncio.get_event_loop()

    dump1090IncomingQueue = asyncio.queues.Queue()
    db_worker_queue       = asyncio.queues.Queue()  # used to send the db_worker messages to work on.


    print('startup: starting')

    dbWorkerTask = loop.create_task(dbWorker(db_worker_queue))
    tasks.append(dbWorkerTask)

    dump1090TCPListenerTask = loop.create_task(dump1090TCPListener(dump1090IncomingQueue, dump1090host, dump1090port))
    tasks.append(dump1090TCPListenerTask)

    dump1090receiverTask = loop.create_task(dump1090Receiver(dump1090IncomingQueue, db_worker_queue))
    tasks.append(dump1090receiverTask)

    monitorTask = loop.create_task(monitor(10))
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