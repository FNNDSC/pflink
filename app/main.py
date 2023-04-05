import  uvicorn
from    pymongo             import MongoClient
#from    .config             import settings
import os
import hashlib

MONGO_DETAILS = os.getenv("PFLINK_MONGODB", "mongodb://localhost:27017")
PFDCM_DETAILS = os.getenv('PFLINK_PFDCM', 'http://localhost:4005')
PORT = int(os.getenv('PFLINK_PORT', '8050'))

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
    pfdcm = retrieve_pfdcm("PFDCMLOCAL")
    if not pfdcm:
        add_pfdcm(
        {
            "service_name": "PFDCMLOCAL",
            "server_ip"   : "http://localhost",
            "server_port" : "4005",
        }
        )
    
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
    
