import requests
import json
import hashlib
from app.config import settings
from pymongo import MongoClient

MONGO_DETAILS = str(settings.pflink_mongodb)
client = MongoClient(MONGO_DETAILS)
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
    pfdcms = [pfdcm["service_name"] for pfdcm in pfdcm_collection.find()]
    return pfdcms


# Add a new pfdcm record into to the database
async def add_pfdcm(pfdcm_data: dict) -> dict:
    """
    DB constraint: Only unique names allowed
    """
    try:
        pfdcm = pfdcm_collection.insert_one(pfdcm_helper(pfdcm_data))
        new_pfdcm = pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
        return pfdcm_helper(new_pfdcm)
    except:
        return {}


# Retrieve a pfdcm record with a matching service name
def retrieve_pfdcm(service_name: str) -> dict:
    pfdcm = pfdcm_collection.find_one({"service_name": service_name})
    if pfdcm:
        return pfdcm_helper(pfdcm)


# Get a 'hello' response from pfdcm
async def hello_pfdcm(service_name: str) -> dict:
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return {"error": f"{service_name} does not exist."}
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_hello_api = f'{pfdcm_url}/api/v1/hello/'
    try:
        response = requests.get(pfdcm_hello_api)
        d_results = json.loads(response.text)
        return d_results
    except:
        return{"error": f"Unable to reach {pfdcm_url}."}


# Get details about pfdcm
async def about_pfdcm(service_name: str) -> dict:
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return {"error": f"{service_name} does not exist."}
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_about_api = f'{pfdcm_url}/api/v1/about/'
    try:
        response = requests.get(pfdcm_about_api)
        d_results = json.loads(response.text)
        return d_results
    except:
        return{"error": f"Unable to reach {pfdcm_url}."}


# Get the list of `cube` available in a pfdcm instance
async def cube_list(service_name: str) -> list[str]:
    d_results = []
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return d_results
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_cube_list_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/list/'
    try:
        response = requests.get(pfdcm_cube_list_api)
        d_results = json.loads(response.text)
        return d_results
    except:
        return d_results


# Get the list of `swift` servers available in a pfdcm instance
async def swift_list(service_name: str) -> list[str]:
    d_results = []
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return d_results
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_swift_list_api = f'{pfdcm_url}/api/v1/SMDB/swift/list/'
    try:
        response = requests.get(pfdcm_swift_list_api)
        d_results = json.loads(response.text)
        return d_results
    except:
        return d_results


# Get the list of `PACS service` available in a pfdcm instance
async def pacs_list(service_name: str) -> list[str]:
    d_results = []
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return d_results
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_pacs_list_api = f'{pfdcm_url}/api/v1/PACSservice/list'
    try:
        response = requests.get(pfdcm_pacs_list_api)
        d_results = json.loads(response.text)
        return d_results
    except:
        return d_results
