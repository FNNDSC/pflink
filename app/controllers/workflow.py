import motor.motor_asyncio
import json
import hashlib
import logging
import subprocess

from .processes.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
    WorkflowDBSchema,
    Error,
)

from controllers.pfdcm import (
    retrieve_pfdcm,
)
from config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.workflows
workflow_collection = database.get_collection("workflows_collection")

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)


# helpers

def test_bg_process():
    print("Running as BG process")


def workflow_retrieve_helper(workflow: dict) -> WorkflowDBSchema:
    request = WorkflowRequestSchema(
        pfdcm_info=workflow["request"]["pfdcm_info"],
        pacs_directive=workflow["request"]["pacs_directive"],
        workflow_info=workflow["request"]["workflow_info"],
    )
    return WorkflowDBSchema(
        key=workflow["_id"],
        request=request,
        response=workflow["response"],
        stale=workflow["stale"],
        started=workflow["started"],
    )


def workflow_add_helper(workflow: WorkflowDBSchema) -> dict:
    d_request = {
        "pfdcm_info": workflow.request.pfdcm_info.__dict__,
        "pacs_directive": workflow.request.pacs_directive.__dict__,
        "workflow_info": workflow.request.workflow_info.__dict__,
    }

    return {
        "_id": workflow.key,
        "request": d_request,
        "response": workflow.response.__dict__,
        "stale": workflow.stale,
        "started": workflow.started,
    }


def query_to_dict(request: WorkflowRequestSchema) -> dict:
    return {
        "pfdcm_info": request.pfdcm_info.__dict__,
        "pacs_directive": request.pacs_directive.__dict__,
        "workflow_info": request.workflow_info.__dict__,
    }


def dict_to_hash(data: dict) -> str:
    # convert to string and encode
    str_data = json.dumps(data)
    hash_request = hashlib.md5(str_data.encode())

    # create a unique key
    key = hash_request.hexdigest()
    return key


def validate_request(request: WorkflowRequestSchema):
    """
    A helper method validate all required fields in a request payload
    """
    error = ""
    attr_count = 0

    if not request.pfdcm_info.pfdcm_service:
        error += "\nPlease enter a `PFDCM` service name"

    for k, v in request.pacs_directive:
        if v:
            attr_count += 1

    if attr_count == 0:
        error += "\nPlease enter at least one value in PACSdirective"

    if not request.workflow_info.user_name:
        error += "\nPlease enter a user name (min 4 characters)"

    if not request.workflow_info.feed_name:
        error += "\nPlease enter a feed name"

    if not request.workflow_info.plugin_name:
        error += "\nPlease enter a Plugin name"

    return error


# DB methods


# Retrieve all workflows present in the DB
async def retrieve_workflows():
    workflows = []
    async for workflow in workflow_collection.find():
        workflows.append(workflow_retrieve_helper(workflow))
    return workflows


# Add new workflow in the DB
async def add_workflow(workflow_data: WorkflowDBSchema) -> dict:
    new_workflow = await workflow_collection.insert_one(workflow_add_helper(workflow_data))
    workflow = await workflow_collection.find_one({"_id": new_workflow.inserted_id})
    return workflow_retrieve_helper(workflow)


def update_workflow(key: str, data: dict):
    """
    Update an existing workflow in the DB
    """
    workflow = workflow_collection.find_one({"_id": key})
    if workflow:
        updated_workflow = workflow_collection.update_one(
            {"_id": key}, {"$set": workflow_add_helper(data)}
        )
        if updated_workflow:
            return True
        return False

    # Retrieve an existing workflow from DB


async def retrieve_workflow(key: str) -> dict:
    workflow = await workflow_collection.find_one({"_id": key})
    if workflow:
        return workflow_retrieve_helper(workflow)


# Retrieve an existing `pfdcm` service address
async def retrieve_pfdcm_url(service_name: str) -> str:
    pfdcm_server = await retrieve_pfdcm(service_name)
    if not pfdcm_server:
        raise Exception(f"Service {service_name} not found in the DB")

    pfdcm_url = pfdcm_server['server_ip'] + ":" + pfdcm_server['server_port']
    return pfdcm_url


# Delete all workflow records from DB
async def delete_workflows():
    delete_count = 0
    async for workflow in workflow_collection.find():
        workflow_collection.delete_one({"_id": workflow["_id"]})
        delete_count += 1
    return {"Message": f"{delete_count} record(s) deleted!"}


# POST a workflow
async def post_workflow(
        data: WorkflowRequestSchema,
        test: bool = False,
        error_type: str = "",
) -> WorkflowStatusResponseSchema:
    """
    Create a new workflow object and
    store it in DB or retrieve if already
    present.
    Start a new subprocess to create a workflow
    Start a new subprocess to update the database
    """
    d_data = query_to_dict(data)
    str_data = json.dumps(d_data)
    key = dict_to_hash(d_data)
    pfdcm_url = ""
    error = validate_request(data)
    response = WorkflowStatusResponseSchema()
    workflow = await retrieve_workflow(key)

    if not workflow:
        new_workflow = WorkflowDBSchema(
            key=key,
            request=data,
            response=response
        )
        workflow = await add_workflow(new_workflow)

    if error or error_type:
        workflow.response.status = False
        try:
            error += Error[error_type].value
        except Exception as err:
            error += f"Undefined error_type {error_type}: " \
                     f"Please pass values as pfdcm/study/feed/analysis/compute/cube " \
                     f"as valid error_type"
        workflow.response.error = error
        return workflow.response

    try:
        if not test:
            pfdcm_url = await retrieve_pfdcm_url(data.pfdcm_info.pfdcm_service)

        status_update = subprocess.Popen(
            ['python',
             'app/controllers/processes/status.py',
             "--data", str_data,
             "--url", pfdcm_url,
             ], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True)

        manage_workflow = subprocess.Popen(
            ['python',
             'app/controllers/processes/wf_manager.py',
             "--data", str_data,
             "--url", pfdcm_url,
             ], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True)

        """
        stderr,stdout = manage_workflow.communicate()
        print(stderr,stdout)
        stderr,stdout = status_update.communicate()
        print(stderr,stdout)
        """




    except Exception as e:
        workflow.response.status = False
        workflow.response.error = str(e)

    return workflow.response
