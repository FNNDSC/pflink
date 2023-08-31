import json
import httpx
import pymongo.results

from app.config import settings
from pymongo import MongoClient

MONGO_DETAILS = str(settings.pflink_mongodb)
client = MongoClient(MONGO_DETAILS, username=settings.mongo_username, password=settings.mongo_password)
database = client.database
pfdcm_collection = database.get_collection("pfdcms_collection")


# helpers


def pfdcm_helper(pfdcm) -> dict:
    return {
        "_id": pfdcm["service_name"],
        "service_name": pfdcm["service_name"],
        "service_address": pfdcm["service_address"],
    }


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
        pfdcm: pymongo.results.InsertOneResult = pfdcm_collection.insert_one(pfdcm_helper(pfdcm_data))
        if pfdcm.acknowledged:
            inserted_pfdcm: dict = pfdcm_collection.find_one({"_id": pfdcm.inserted_id})
            return inserted_pfdcm
        else:
            raise Exception("Could not store new record.")
    except Exception as ex:
        return {"error": str(ex)}


# Retrieve a pfdcm record with a matching service name
def retrieve_pfdcm(service_name: str) -> dict:
    pfdcm = pfdcm_collection.find_one({"service_name": service_name})
    if pfdcm:
        return pfdcm_helper(pfdcm)
        
        
# Get a 'hello' response from pfdcm
async def hello_pfdcm(pfdcm_name: str) -> dict:
    pfdcm_server = retrieve_pfdcm(pfdcm_name)
    if not pfdcm_server:
        return {"Error": f"Service {pfdcm_name} not found in the DB"}
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_hello_api = f'{pfdcm_url}/hello/'
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(pfdcm_hello_api)
            d_results = json.loads(response.text)
            return d_results
        except Exception as ex:
            return {"error": f"Unable to reach {pfdcm_url}.{ex}"}


async def about_pfdcm(service_name: str) -> dict:
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return {"error": f"{service_name} does not exist."}
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_about_api = f'{pfdcm_url}/about/'
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(pfdcm_about_api)
            d_results = json.loads(response.text)
            return d_results
        except:
            return {"error": f"Unable to reach {pfdcm_url}."}


# Get the list of `cube` available in a pfdcm instance
async def cube_list(service_name: str) -> list[str]:
    d_results = []
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return d_results
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_cube_list_api = f'{pfdcm_url}/SMDB/CUBE/list/'
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(pfdcm_cube_list_api)
            d_results = json.loads(response.text)
            return d_results
        except:
            return d_results


# Get the list of `storage` services available in a pfdcm instance
async def storage_list(service_name: str) -> list[str]:
    d_results = []
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        return d_results
    pfdcm_url = pfdcm_server['service_address']
    pfdcm_storage_list_api = f'{pfdcm_url}/SMDB/storage/list/'
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(pfdcm_storage_list_api)
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
    pfdcm_pacs_list_api = f'{pfdcm_url}/PACSservice/list/'
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(pfdcm_pacs_list_api)
            d_results = json.loads(response.text)
            return d_results
        except:
            return d_results


async def delete_pfdcm(service_name: str):
    """
    Delete a pfdcm record from the DB
    """
    delete_count = 0
    for pfdcm in pfdcm_collection.find():
        if pfdcm["_id"] == service_name:
            pfdcm_collection.delete_one({"_id": pfdcm["_id"]})
            delete_count += 1
    return {"Message": f"{delete_count} record(s) deleted!"}

