import motor.motor_asyncio
from bson.objectid import ObjectId
import requests
import json

MONGO_DETAILS = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

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

# Retrieve all pfdcm present in the database
async def retrieve_pfdcms():
    pfdcms = []
    async for pfdcm in pfdcm_collection.find():
        pfdcms.append(pfdcm_helper(pfdcm))
    return pfdcms


# Add a new pfdcm into to the database
async def add_pfdcm(pfdcm_data: dict) -> dict:
    pfdcm = await pfdcm_collection.insert_one(pfdcm_data)
    new_pfdcm = await pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
    return pfdcm_helper(new_pfdcm)


# Retrieve a pfdcm with a matching service name
async def retrieve_pfdcm(service_name: str) -> dict:
    pfdcm = await pfdcm_collection.find_one({"service_name": service_name})
    if pfdcm:
        return pfdcm_helper(pfdcm)
        
# Get a 'hello' response from pfdcm
async def hello_pfdcm(pfdcm : dict) -> dict:
    pfdcm_name = pfdcm.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    pfdcm_hello_api = f'{pfdcm_url}/api/v1/hello/'
    response = requests.get(pfdcm_hello_api)
    d_results = json.loads(response.text)
    return d_results

# Get details about pfdcm
async def about_pfdcm(pfdcm : dict) -> dict:
    pfdcm_name = pfdcm.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    pfdcm_about_api = f'{pfdcm_url}/api/v1/about/'    
    response = requests.get(pfdcm_about_api)
    d_results = json.loads(response.text)
    return d_results
