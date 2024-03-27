from app.controllers.subprocesses.utils import (
    get_cube_url_from_pfdcm,
    do_cube_create_user,
    retrieve_pfdcm_url,
)
from app.models import cube
import requests
import json


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


