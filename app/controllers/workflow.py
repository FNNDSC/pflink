from pymongo import MongoClient
import json
import logging
import subprocess

from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
    WorkflowDBSchema,
    Error,
)
from app.controllers.subprocesses import utils
from app.config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)
client = MongoClient(MONGO_DETAILS)
database = client.workflows
workflow_collection = database.get_collection("workflows_collection")

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)


# DB methods


# Retrieve all workflows present in the DB
def retrieve_workflows():
    workflows = []
    for workflow in workflow_collection.find():
        workflows.append(utils.workflow_retrieve_helper(workflow))
    return workflows


# Add new workflow in the DB
def add_workflow(workflow_data: WorkflowDBSchema) -> WorkflowDBSchema:
    new_workflow = workflow_collection.insert_one(utils.workflow_add_helper(workflow_data))
    workflow = workflow_collection.find_one({"_id": new_workflow.inserted_id})
    return utils.workflow_retrieve_helper(workflow)


def delete_workflow(request: dict):
    """
    Delete a workflow record from DB
    """
    delete_count = 0
    key = utils.dict_to_hash(request)
    for workflow in workflow_collection.find():
        if workflow["_id"] == key:
            workflow_collection.delete_one({"_id": workflow["_id"]})
            delete_count += 1
    return {"Message": f"{delete_count} record(s) deleted!"}


def request_to_hash(request: WorkflowRequestSchema) -> str:
    """
    Create a hash key using md5 hash function on a workflow request object
    """
    d_data = utils.query_to_dict(request)
    key = utils.dict_to_hash(d_data)
    return key


async def post_workflow(
        request: WorkflowRequestSchema,
        test: bool = False,
        error_type: str = "",
) -> WorkflowStatusResponseSchema:
    """
    The purpose of this method is to create a new workflow object in the DB if not already present.
    This method then starts two independent subprocesses in the background:
        1) Run a new subprocess to manage the workflow
        2) Run a new subprocess to update the status of the workflow
    Finally, return the current status of the workflow from the database
    """
    # create a hash key using the request
    request_hash = request_to_hash(request)
    db_key = request_hash+request.cube_user_info.username
    workflow = utils.retrieve_workflow(db_key)
    if not workflow:
        duplicates = check_for_duplicates(request_hash)
        if duplicates and not request.ignore_duplicate:
            return duplicates[0].response
        workflow = create_new_workflow(db_key, request)

    # 'error_type' is an optional test-only parameter that forces the workflow to error out
    # at a given error state
    if error_type:
        return create_response_with_error(error_type, workflow.response)

    mode, str_data = get_suproc_params(test, request)
    # run workflow manager subprocess on the workflow
    sub_mng = manage_workflow(str_data, mode)

    # run status_update subprocess on the workflow
    sub_updt = update_workflow_status(str_data, mode)
    # debug_process(sub_updt)
    return workflow.response


def create_new_workflow(key: str, request: WorkflowRequestSchema, response=WorkflowStatusResponseSchema()):
    """Create a new workflow object and add it to the database"""
    new_workflow = WorkflowDBSchema(key=key, request=request, response=response)
    workflow = add_workflow(new_workflow)
    return workflow


def create_response_with_error(
        error_type: str,
        response: WorkflowStatusResponseSchema
) -> WorkflowStatusResponseSchema:
    """
    This is a test-only method that sets the response of a workflow
    to an error state
    """
    response.status = False
    try:
        response.error = Error[error_type]
    except:
        response.error = Error.undefined
    return response


def manage_workflow(str_data: str, mode: str):
    """
    Manage a workflow request in a separate subprocess
    """
    d_cmd = ["python", "app/controllers/subprocesses/wf_manager.py", "--data", str_data]
    if mode:
        d_cmd.append(mode)
    subproc = subprocess.Popen(d_cmd)
    return subproc


def update_workflow_status(str_data: str, mode: str):
    """
    Update the current status of a workflow request in a separate process
    """
    d_cmd = ["python", "app/controllers/subprocesses/status.py", "--data", str_data]
    if mode:
        d_cmd.append(mode)
    subproc = subprocess.Popen(d_cmd)
    return subproc


def debug_process(bgprocess):
    """
    A blocking method to communicate with a background process and print stdout & stderr
    """
    stderr, stdout = bgprocess.communicate()
    print(stderr, stdout)


def check_for_duplicates(request_hash: str) -> list[WorkflowDBSchema]:
    """
    Check for duplicate workflow request made by a user
      A workflow request is a duplicate request if there exists one or more entries in the DB of similar
      footprint.
    """
    workflows = [workflow for workflow in workflow_collection.find({"footprint": request_hash})]
    return workflows


def get_suproc_params(test: bool, request: WorkflowRequestSchema) -> (str, str):
    """
    Return mode, str_data
    """
    mode = ""
    if test:
        mode = "--test"
    d_data = utils.query_to_dict(request)
    str_data = json.dumps(d_data)
    return mode, str_data
