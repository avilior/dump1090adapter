import asyncio
import traceback
from dump1090processor.dump1090receiver import INCOMING_ACTION_TYPE
from starlette.websockets import WebSocket, WebSocketState

async def websocketBroadcaster(websocket_clients, websocket_queue):
    print("WEBSOCKET BROADCASTER starting")
    while True:
        try:
            msg:INCOMING_ACTION_TYPE = await websocket_queue.get()
            # iterate over the websocket_clients sending them the message
            #print(F"WS_BROADCAST rx: {msg}")

            rec = msg.actionMsg # this is a JSON message

            payload = { **rec['current']}

            payload["icao24"] = msg.aircraftId
            payload["ts"] = str(rec['last_seen'])

            msg = { 'type': "radarUpdate", 'payload':payload}

            #print(F"WS_BROADCAST msg to send: {to_send}")

            for netloc, context in websocket_clients.items():
                ws : WebSocket = context['ws']

                if ws.client_state ==  WebSocketState.CONNECTED:
                    #print(F"Sending to {netloc}")
                    await ws.send_json(msg)

        except asyncio.CancelledError:
            print("Canceled dump period")
            break
        except Exception as x:
            traceback.print_exc()
            print(F"websocket: Connection closed {x}")

    print("WEBSOCKET BROADCASTER STOPPED")
