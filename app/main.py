import  uvicorn
from    pymongo             import MongoClient
import os

MONGO_DETAILS = os.getenv("PFLINK_MONGODB", "mongodb://localhost:27017")
PFDCM_DETAILS = os.getenv('PFLINK_PFDCM', 'http://localhost:4005')
PORT = int(os.getenv('PFLINK_PORT', '8050'))

client = MongoClient(MONGO_DETAILS)

database = client.pfdcms

pfdcm_collection = database.get_collection("pfdcms_collection")

# helpers


def pfdcm_helper(pfdcm):
    return {
        "id"          : str(pfdcm["_id"]),
        "service_name": pfdcm["service_name"],
        "server_ip"   : pfdcm["server_ip"],
        "server_port" : pfdcm["server_port"],
    }
    
# Add a new pfdcm into to the database
def add_pfdcm(pfdcm_data):
    pfdcm = pfdcm_collection.insert_one(pfdcm_data)
    new_pfdcm = pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
    return pfdcm_helper(new_pfdcm)
    
    
        
if __name__ == "__main__":
    add_pfdcm(
        {
            "service_name": "PFDCMLOCAL",
            "server_ip"   : PFDCM_DETAILS.split(':')[0],
            "server_port" : PFDCM_DETAILS.split(':')[-1],
        }
    )
    
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
    
