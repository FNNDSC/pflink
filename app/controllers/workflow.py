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


def workflow_retrieve_helper(workflow: dict) -> WorkflowDBSchema:
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


def workflow_add_helper(workflow: WorkflowDBSchema) -> dict:
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


def validate_request(request: WorkflowRequestSchema, error_type: str):
    """
    A helper method validate all required fields in a request payload
    """
    error = ""
    attr_count = 0

    if not request.pfdcm_info.pfdcm_service:
        error += f"\n{Error.required_pfdcm.value}"

    if not request.pfdcm_info.PACS_service:
        error += f"\n{Error.required_PACS.value}"

    if not request.pfdcm_info.cube_service:
        error += f"\n{Error.required_cube.value}"

    for k, v in request.PACS_directive:
        if v:
            attr_count += 1

    if attr_count == 0:
        error += f"\n{Error.required_directive.value}"

    if not request.workflow_info.user_name:
        error += f"\n{Error.required_user.value}"

    if not request.workflow_info.feed_name:
        error += f"\n{Error.required_feed.value}"

    if not request.workflow_info.plugin_name:
        error += f"\n{Error.required_plugin.value}"

    if error_type:
        try:
            error += f"\n{Error[error_type].value}"
        except:
            error += f"\n{Error.undefined.value}"

    return error


# DB methods


# Retrieve all workflows present in the DB
async def retrieve_workflows():
    workflows = []
    async for workflow in workflow_collection.find():
        workflows.append(workflow_retrieve_helper(workflow))
    return workflows


# Add new workflow in the DB
async def add_workflow(workflow_data: WorkflowDBSchema) -> WorkflowDBSchema:
    new_workflow = await workflow_collection.insert_one(workflow_add_helper(workflow_data))
    workflow = await workflow_collection.find_one({"_id": new_workflow.inserted_id})
    return workflow_retrieve_helper(workflow)


def update_workflow(key: str, data: WorkflowDBSchema) -> bool:
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


async def retrieve_workflow(key: str) -> WorkflowDBSchema:
    """
    Retrieve an existing workflow from DB
    """
    workflow = await workflow_collection.find_one({"_id": key})
    if workflow:
        return workflow_retrieve_helper(workflow)


async def delete_workflows():
    """
    Delete all workflow records from DB
    """
    delete_count = 0
    async for workflow in workflow_collection.find():
        workflow_collection.delete_one({"_id": workflow["_id"]})
        delete_count += 1
    return {"Message": f"{delete_count} record(s) deleted!"}


def request_to_hash(request: WorkflowRequestSchema) -> str:
    """
    Create a hash key using md5 hash function on a workflow request object
    """
    d_data = query_to_dict(request)
    key = dict_to_hash(d_data)
    return key


async def post_workflow(
        request: WorkflowRequestSchema,
        test: bool = False,
        error_type: str = "",
) -> WorkflowStatusResponseSchema:
    """
    The purpose of this method is to create a new workflow object in the DB if not already present.
    If an object already exists, return the current status of the workflow
    Start a new subprocess to create a workflow
    Start a new subprocess to update the database
    """
    # create a hash key using the request
    db_key = request_to_hash(request)
    workflow = await retrieve_workflow(db_key)
    if not workflow:
        # create a new workflow object
        response = WorkflowStatusResponseSchema()
        new_workflow = WorkflowDBSchema(key=db_key, request=request, response=response)
        workflow = await add_workflow(new_workflow)

    # validate request for errors
    # error_type is an optional test-only parameter that forces the workflow to error out
    # at a given error state
    error = validate_request(request, error_type)
    if error:
        workflow.response.status = False
        workflow.response.error = error
        return workflow.response

    mode, str_data = await get_suproc_params(test, request)
    # run workflow manager subprocess on the workflow
    sub_mng = manage_workflow(mode, str_data)

    # run status_update subprocess on the workflow
    sub_updt = update_workflow_status(mode, str_data)
    debug_process(sub_updt)
    return workflow.response


def manage_workflow(mode: str, str_data: str):
    """
    Manage a workflow request in a separate subprocess
    """
    subproc = subprocess.Popen(
        ['python',
         'app/controllers/processes/wf_manager.py',
         "--data", str_data,
         "--test", mode,
         ], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    return subproc


def update_workflow_status(mode: str, str_data: str):
    """
    Update the current status of a workflow request in a separate process
    """
    subproc = subprocess.Popen(
        ['python',
         'app/controllers/processes/status.py',
         "--data", str_data,
         "--test", mode,
         ], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    return subproc


def debug_process(bgprocess):
    stderr, stdout = bgprocess.communicate()
    print(stderr, stdout)


async def get_suproc_params(test: bool, request: WorkflowRequestSchema) -> (str, str):
    """
    Return mode, str_data
    """
    mode = ""
    if test:
        mode = "testing"
    d_data = query_to_dict(request)
    str_data = json.dumps(d_data)
    return mode, str_data
