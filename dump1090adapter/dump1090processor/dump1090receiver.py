import logging
from asyncio.queues import Queue
from asyncio import CancelledError
from dump1090adapter.store.sbs1 import SBS1Message
from dump1090adapter.store.store import process2, dump_row, db2, SBS1Changed
from collections import namedtuple

INCOMING_ACTION_TYPE = namedtuple('IncomingAction',['actionTypes','actionMsg', 'aircraftId'])

LOG = logging.getLogger("dump1090Receiver")


async def dump1090Receiver(incomingQ: Queue, db_worker_Q: Queue = None, radar_Q = None):
    """
        Receive a raw mesage from a Queue parse it sent it to the database_worker (if queue is not None) process the message otherwise)

    :param incomingQ: incoming messaged from 1090
    :param db_worker_Q: queue to send processed messages to db layer -- if not None
    :param radar_Q: queue to send processed messages to radar -- if not None
    :return:
    """
    try:
        while True:
            raw_sbs1_msg = await incomingQ.get()
            #print(f"{raw_item}")

            sbs1_msg = SBS1Message(raw_sbs1_msg)
            if sbs1_msg.isValid:

                #process(sbs1_msg)

                result = process2(sbs1_msg)
                if result is None:
                    continue

                # higher level
                new_aircraft = result.new_aircraft
                position     = any([result.callsign, result.squawk, result.altitude, result.ground_speed, result.track, result.lat, result.lon, result.vertical_rate, result.on_ground])
                emergency    = any([result.alert, result.emergency])


                if any([new_aircraft, position, emergency]):
                    #print(F"[{sbs1_msg.messageType}{sbs1_msg.transmissionType}] New Aircraft: {new_aircraft} Position: {position} Emergency: {emergency}")
                    #dump_row(db2, sbs1_msg.icao24)

                    actionTypesList = []
                    if new_aircraft:
                        actionTypesList.append("new_aircraft")
                    if position:
                        actionTypesList.append("position")
                    if emergency:
                        actionTypesList.append("emergency")

                    incoming_action = INCOMING_ACTION_TYPE(actionTypes=actionTypesList, actionMsg=result.icao_record, aircraftId=sbs1_msg.icao24)

                    if db_worker_Q:
                        db_worker_Q.put_nowait(incoming_action)

                    if radar_Q:
                        radar_Q.put_nowait(incoming_action)

            else:
                print("WARN: Invalid sbs1_msg. Failed processing")

    except CancelledError:
        pass
    except Exception as x:
        print(F"Exception {x}")
    finally:
        pass