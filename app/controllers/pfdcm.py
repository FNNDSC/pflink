import motor.motor_asyncio
import requests
import json
import hashlib
from app.config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.pfdcms
pfdcm_collection = database.get_collection("pfdcms_collection")


# helpers


def pfdcm_helper(pfdcm) -> dict:
    key = str_to_hash(pfdcm["service_name"])
    return {
        "_id": key,
        "service_name": pfdcm["service_name"],
        "service_address": pfdcm["service_address"],
    }


def str_to_hash(str_data: str) -> str:
    hash_request = hashlib.md5(str_data.encode())
    key = hash_request.hexdigest()
    return key
    
    
# Retrieve all pfdcm records present in the database
async def retrieve_pfdcms():
    pfdcms = []
    async for pfdcm in pfdcm_collection.find():
        pfdcms.append(pfdcm_helper(pfdcm))
    return pfdcms


# Add a new pfdcm record into to the database
async def add_pfdcm(pfdcm_data: dict) -> dict:
    """
    DB constraint: Only unique names allowed
    """
    try:
        pfdcm = await pfdcm_collection.insert_one(pfdcm_helper(pfdcm_data))
        new_pfdcm = await pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
        return pfdcm_helper(new_pfdcm)
    except:
        return {}


# Retrieve a pfdcm record with a matching service name
async def retrieve_pfdcm(service_name: str) -> dict:
    pfdcm = await pfdcm_collection.find_one({"service_name": service_name})
    if pfdcm:
        return pfdcm_helper(pfdcm)


# Get a 'hello' response from pfdcm
async def hello_pfdcm(service_name: str) -> dict:
    pfdcm_server = await retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return {"error": f"{service_name} does not exist."}
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_hello_api = f'{pfdcm_url}/api/v1/hello/'
    response = requests.get(pfdcm_hello_api)
    d_results = json.loads(response.text)
    return d_results


# Get details about pfdcm
async def about_pfdcm(service_name: str) -> dict:
    pfdcm_server = await retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return {"error": f"{service_name} does not exist."}
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_about_api = f'{pfdcm_url}/api/v1/about/'    
    response = requests.get(pfdcm_about_api)
    d_results = json.loads(response.text)
    return d_results

