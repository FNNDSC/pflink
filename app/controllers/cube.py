import pymongo.results
from app.config import settings
from pymongo import MongoClient
from app.controllers.subprocesses.utils import (
    get_cube_url_from_pfdcm,
    do_cube_create_user,
    retrieve_pfdcm_url,
)
from app.models import cube
import requests
import json
from typing import List

MONGO_DETAILS = str(settings.pflink_mongodb)
client = MongoClient(MONGO_DETAILS, username=settings.mongo_username, password=settings.mongo_password)
database = client.database
cube_collection = database.get_collection("cubes_collection")


# helper methods to add and retrieve

def cube_add_helper(cube_data: cube.CubeService) -> dict:
    return {
        "_id": cube_data["service_name"],
        "service_URL": cube_data["service_URL"],
    }


async def get_plugins(pfdcm: str, cube_name: str):
    try:
        client = get_cube_client(pfdcm, cube_name)
        resp = client.getPlugins()
        plugins = []
        for item in resp["data"]:
            plugin = cube.Plugin(name=item['name'], version=item['version'])
            plugins.append(plugin)
        return plugins
    except Exception as ex:
        raise Exception(str(ex))


def get_pipelines(pfdcm: str, cube_name: str):
    try:
        client = get_cube_client(pfdcm, cube_name)
        resp = client.getPipelines()
        pipelines = []
        for item in resp["data"]:
            pipelines.append(item["name"])
        return pipelines
    except Exception as ex:
        raise Exception(str(ex))


def get_cube_client(pfdcm: str, cube_name: str):
    try:
        pfdcm_url = retrieve_pfdcm_url(pfdcm)
        pfdcm_smdb_cube_api = f'{pfdcm_url}/SMDB/CUBE/{cube_name}/'
        response = requests.get(pfdcm_smdb_cube_api)
        d_results = json.loads(response.text)
        if not d_results["status"]:
            raise Exception(f"cube_name {cube_name} is not a valid resource name.")
        cube_url = d_results['cubeInfo']['url']
        username = d_results['cubeInfo']['username']
        password = d_results['cubeInfo']['password']
        client = do_cube_create_user(cube_url, username, password)
        return client
    except Exception as ex:
        raise Exception(ex)


def add_cube_service(cube_service_data: cube.CubeService) -> dict:
    """
    DB constraint: Only unique names allowed
    """
    try:
        cube_svc: pymongo.results.InsertOneResult = cube_collection.insert_one(cube_add_helper(cube_service_data))
        if cube_svc.acknowledged:
            inserted_cube_svc: dict = cube_collection.find_one({"_id": cube_svc.inserted_id})
            return inserted_cube_svc
        else:
            raise Exception("Could not store new record.")
    except Exception as ex:
        return {"error": str(ex)}


def delete_cube_service(service_name: str) -> bool:
    """Remove an existing cube service"""
    pass


def update_cube_service(service_name: str, new_data: dict) -> dict:
    """Update an existing cube service"""
    pass


def retrieve_cube_service(service_name: str) -> dict:
    """Retrieve an existing cube service entry from the DB"""
    pass


def retrieve_cube_services() -> List[str]:
    """Retrieve all the cube services present in the DB"""
    pass
