import uvicorn
from pymongo import MongoClient

MONGO_DETAILS = "mongodb://localhost:27017"

client = MongoClient(MONGO_DETAILS)

database = client.pfdcms

pfdcm_collection = database.get_collection("pfdcms_collection")

# helpers


def pfdcm_helper(pfdcm) -> dict:
    return {
        "id": str(pfdcm["_id"]),
        "service_name": pfdcm["service_name"],
        "server_ip"   : pfdcm["server_ip"],
        "server_port" : pfdcm["server_port"],
    }
    
# Add a new pfdcm into to the database
def add_pfdcm(pfdcm_data: dict) -> dict:
    pfdcm = pfdcm_collection.insert_one(pfdcm_data)
    new_pfdcm = pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
    return pfdcm_helper(new_pfdcm)
    
    
        
if __name__ == "__main__":
    add_pfdcm(
        {
            "service_name": "PFDCMLOCAL",
            "server_ip"   : "http://localhost",
            "server_port" : "4005",
        }
    )
    
    uvicorn.run("app:app", host="localhost", port=8050, reload=True)
    




