from asyncio.streams import open_connection
from asyncio.queues import Queue
from asyncio import CancelledError

import logging

LOG = logging.getLogger("dump1090TCPListener")

STATS = { "msg_rx" : 0, "max_incomingQ_size" : 0, 'connection_closed' : False, "connections" : 0, 'connections_exception': 0}

async def dump1090TCPListener(incomingQ: Queue, host: str, port:int):

    print("dump_receiver starting")
    LOG.info(F"Opening TCP Stream to Dump Server at: {host}:{port}")

    while True:

        try:
            stream_reader, _ = await open_connection(host, port)
            STATS['connection_closed'] = False
            STATS['connections'] += 1
        except Exception as x:
            print(F"@dump1090TCPListener: Got exception {x}")
            LOG.exception(x)
            STATS['connections_exception'] += 1
            continue

        print("Got stream_reader")
        try:
            BUFSIZE = 1024
            data = ""
            while True:
                new_data = await stream_reader.read(BUFSIZE)

                if not new_data:
                    LOG.info("receiver: connection closed")
                    STATS['connection_closed'] = True
                    return
                    # break it into lines

                data += new_data.decode('utf-8')

                #print(F"#######\n{data}######")

                cur_pos = 0
                while True:

                    # print(F"DATA\n{data}\n")

                    cr_index = data.find('\n')

                    if cr_index > 0:
                        # print(F"Slice {cur_pos} : {cr_index} Data: {data[cur_pos:cr_index]}")

                        l = data[cur_pos:cr_index].strip()
                        #print(F"Q<-{l}\n", end='')
                        incomingQ.put_nowait(l)
                        STATS["msg_rx"] += 1
                        STATS["max_incomingQ_size"] = max(incomingQ.qsize(),STATS["max_incomingQ_size"])
                        # print(F"done")

                        cur_pos = cr_index + 1
                        data = data[cur_pos:]
                        cur_pos = 0
                    else:
                        # print(F"Slice {cur_pos} : {cr_index} Data: {data[cur_pos:cr_index]}")
                        break

        except CancelledError:
            print("Cancelled exception.  Cancelling dump1090TCPListener")
            break
        except Exception as x:
            LOG.exception(x)
            print(F"Got exception {x}")
        finally:
            pass

    print(F"Exiting dump1090TCPListener")