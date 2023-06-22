from app.controllers.subprocesses.utils import (
    get_cube_url_from_pfdcm,
    do_cube_create_user,
    retrieve_pfdcm_url,
)
import requests
import json

def get_plugins(pfdcm: str, cube_name: str):
    client = get_cube_client(pfdcm, cube_name)
    resp = client.getPlugins()
    plugins = []
    for item in resp["data"]:
        plugins.append(item["name"])
    return plugins

def get_pipelines(pfdcm: str, cube_name: str):
    client = get_cube_client(pfdcm, cube_name)
    resp = client.getPipelines()
    pipelines = []
    for item in resp["data"]:
        pipelines.append(item["name"])
    return pipelines


def get_cube_client(pfdcm: str, cube_name: str):
    pfdcm_url = retrieve_pfdcm_url(pfdcm)
    pfdcm_smdb_cube_api = f'{pfdcm_url}/SMDB/CUBE/{cube_name}/'
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text)
    cube_url = d_results['cubeInfo']['url']
    username = d_results['cubeInfo']['username']
    password = d_results['cubeInfo']['password']
    client = do_cube_create_user(cube_url, username, password)
    return client


