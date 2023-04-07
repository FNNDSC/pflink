import  uvicorn
from    pymongo             import MongoClient
import os
import hashlib
from config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)
PFDCM_DETAILS = str(settings.pflink_pfdcm)
PFDCM_NAME    = settings.pfdcm_name
PORT          = settings.pflink_port

client           = MongoClient(MONGO_DETAILS)

database         = client.pfdcms

pfdcm_collection = database.get_collection("pfdcms_collection")

# helpers


def pfdcm_helper(pfdcm):
    key = str_to_hash(pfdcm["service_name"])
    return {
        "_id"         : key,
        "service_name": pfdcm["service_name"],
        "server_ip"   : pfdcm["server_ip"],
        "server_port" : pfdcm["server_port"],
    }
    
def str_to_hash(str_data:str) -> str:
    hash_request = hashlib.md5(str_data.encode())
    key          = hash_request.hexdigest()
    return key
    
# Add a new pfdcm into to the database
def add_pfdcm(pfdcm_data):
    pfdcm = pfdcm_collection.insert_one(pfdcm_helper(pfdcm_data))
    new_pfdcm = pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
    return pfdcm_helper(new_pfdcm)

# Retrieve a pfdcm with a matching service name
def retrieve_pfdcm(service_name: str) -> dict:
    pfdcm = pfdcm_collection.find_one({"service_name": service_name})
    if pfdcm:
        return pfdcm_helper(pfdcm)    
    
        
if __name__ == "__main__":
    pfdcm = retrieve_pfdcm(PFDCM_NAME)
    if not pfdcm:
        # FIXME yo-yo code
        # pfdcm URL is unnecessarily split into port and IP,
        # where referenced these two values are always just joined back together.
        pfdcm_port = settings.pflink_pfdcm.port
        # FIXME misleading variable name
        # References of this value expect `pfdcm_ip` to have the scheme prefixed, i.e.
        # it's always passed to `requests.get` which requires the value to start with "http://" (or similar)
        pfdcm_ip   = f'{settings.pflink_pfdcm.scheme}://{settings.pflink_pfdcm.host}'
        add_pfdcm(
        {
            "service_name":  PFDCM_NAME,
            "server_ip"   :  pfdcm_ip,
            "server_port" :  pfdcm_port,
        }
        )
    
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
    
