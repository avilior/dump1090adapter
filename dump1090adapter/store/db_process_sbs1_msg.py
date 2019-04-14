
from dump1090adapter.store.sbs1 import SBS1Message
import aiosqlite

def prepare_db():
    pass

def db_process_sbs1_msg(msg: SBS1Message):

    #msg.dump()
    #print(msg.icao24)
    #print(msg.generatedDate)

    # get the database record for the icao
    #print(F"Fetching database record for icao24")
    pass
