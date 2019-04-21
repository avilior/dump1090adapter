import asyncio
from dump1090adapter.store.store import dump_store
import traceback
async def monitor(period: int):
    while True:
        try:
            await asyncio.sleep(period)
            dump_store()

        except asyncio.CancelledError:
            print("Canceled dump period")
            break
        except Exception:
            traceback.print_exc()
