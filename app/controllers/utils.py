import hashlib
import json
import requests
from app.controllers.python_chris_client import PythonChrisClient
from pymongo import MongoClient
from app.config import settings
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowDBSchema,
)
from app.controllers.pfdcm import (
    retrieve_pfdcm
)
MONGO_DETAILS = str(settings.pflink_mongodb)

client = MongoClient(MONGO_DETAILS)

database = client.workflows
pfdcm_database = client.pfdcms

workflow_collection = database.get_collection("workflows_collection")
pfdcm_collection = pfdcm_database.get_collection("pfdcms_collection")


# helpers


def str_to_hash(str_data: str) -> str:
    hash_request = hashlib.md5(str_data.encode())
    key = hash_request.hexdigest()
    return key


def _workflow_retrieve_helper(workflow: dict) -> WorkflowDBSchema:
    request = WorkflowRequestSchema(
                   pfdcm_info=workflow["request"]["pfdcm_info"],
                   PACS_directive=workflow["request"]["PACS_directive"],
                   workflow_info=workflow["request"]["workflow_info"],
               )
    return WorkflowDBSchema(
        key=workflow["_id"],
        request=request,
        response=workflow["response"],
        stale=workflow["stale"],
        started=workflow["started"],
    )


def _workflow_add_helper(workflow: WorkflowDBSchema) -> dict:
    d_request = {
        "pfdcm_info": workflow.request.pfdcm_info.__dict__,
        "PACS_directive": workflow.request.PACS_directive.__dict__,
        "workflow_info": workflow.request.workflow_info.__dict__,
    }
    
    return {
        "_id": workflow.key,
        "request": d_request,
        "response": workflow.response.__dict__,
        "stale": workflow.stale,
        "started": workflow.started,
    }


def dict_to_query(request: dict) -> WorkflowRequestSchema:
    return WorkflowRequestSchema(
        pfdcm_info=request["pfdcm_info"],
        PACS_directive=request["PACS_directive"],
        workflow_info=request["workflow_info"],
    )


def query_to_dict(request: WorkflowRequestSchema) -> dict:
    return {
        "pfdcm_info": request.pfdcm_info.__dict__,
        "PACS_directive": request.PACS_directive.__dict__,
        "workflow_info": request.workflow_info.__dict__,
    }


def dict_to_hash(data: dict) -> str:
    # convert to string and encode
    str_data = json.dumps(data)
    hash_request = hashlib.md5(str_data.encode())     
    # create a unique key
    key = hash_request.hexdigest()
    return key

# DB queries

                   
def update_workflow(key: str, data: WorkflowDBSchema) -> bool:
    """
    Update an existing workflow in the DB
    """
    workflow = workflow_collection.find_one({"_id": key})
    if workflow:
        updated_workflow = workflow_collection.update_one(
            {"_id": key}, {"$set": _workflow_add_helper(data)}
        )
        if updated_workflow:
            return True
        return False


def retrieve_workflow(key: str) -> WorkflowDBSchema:
    """
    Retrieve a single workflow from DB
    Given: key
    """
    workflow = workflow_collection.find_one({"_id": key})
    if workflow:
        return _workflow_retrieve_helper(workflow)


def retrieve_pfdcm_url(service_name: str) -> str:
    """
    # Retrieve an existing `pfdcm` service address
    """
    pfdcm_server = retrieve_pfdcm(service_name)
    if not pfdcm_server:
        raise Exception(f"Service {service_name} not found in the DB")

    pfdcm_url = pfdcm_server['service_address']
    return pfdcm_url


def get_cube_url_from_pfdcm(pfdcm_url: str, cube_name: str) -> str:
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cube_name}/'
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text)
    cube_url = d_results['cubeInfo']['url']
    return cube_url


def substitute_dicom_tags(
        text: str,
        dicom_data: dict
) -> str:
    """
    # Given a string containing dicom tags separated by `%`, substitute dicom values
    # for those dicom tags from a given dictionary if present
    """
    text_w_values = ""
    items = text.split('%')

    for item in items:
        if item == "":
            continue
        tags = item.split('-')
        dicom_tag = tags[0]

        try:
            dicom_value = dicom_data[dicom_tag]
        except:
            dicom_value = dicom_tag
        item = item.replace(dicom_tag, dicom_value)
        text_w_values = text_w_values + item

    return text_w_values


def _do_cube_create_user(cube_url: str, user_name: str) -> PythonChrisClient:
    """
    Create a new user in `CUBE` if not already present
    """
    create_user_url = cube_url + "users/"
    user_pass = user_name + "1234"
    user_email = user_name + "@email.com"

    # create a new user
    headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
    body = {"username": user_name, "password": user_pass, "email": user_email}
    resp = requests.post(create_user_url, json=body, headers=headers)

    # create a cube client
    cube_client = PythonChrisClient(cube_url, user_name, user_pass)
    return cube_client

