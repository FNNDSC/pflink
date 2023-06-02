from pymongo import MongoClient
import json
import logging
import subprocess

from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
    WorkflowDBSchema,
    Error,
    UserResponseSchema,
)
from app.controllers.subprocesses import utils
from app.config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)
client = MongoClient(MONGO_DETAILS)
database = client.database
workflow_collection = database.get_collection("workflows_collection")
test_collection = database.get_collection("tests_collection")

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)


# DB methods


# Retrieve all workflows present in the DB
def retrieve_workflows(test: bool = False):
    collection = test_collection if test else workflow_collection
    workflows = []
    for workflow in collection.find():
        workflows.append(utils.workflow_retrieve_helper(workflow))
    return workflows


# Add new workflow in the DB
def add_workflow(workflow_data: WorkflowDBSchema, test: bool = False) -> WorkflowDBSchema:
    collection = test_collection if test else workflow_collection
    new_workflow = collection.insert_one(utils.workflow_add_helper(workflow_data))
    workflow = collection.find_one({"_id": new_workflow.inserted_id})
    return utils.workflow_retrieve_helper(workflow)


async def delete_workflows(test: bool = False):
    """
    Delete a workflow record from DB
    """
    collection = test_collection if test else workflow_collection
    delete_count = 0
    for workflow in collection.find():
        collection.delete_one({"_id": workflow["_id"]})
        delete_count += 1
    return {"Message": f"{delete_count} record(s) deleted!"}


def request_to_hash(request: WorkflowRequestSchema) -> str:
    """
    Create a hash key using md5 hash function on a workflow request object
    """
    d_data = utils.request_to_dict(request)
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
    db_key = request_to_hash(request)
    workflow = utils.retrieve_workflow(db_key, test)
    if not workflow:
        fingerprint = get_fingerprint(request)
        duplicates = check_for_duplicates(fingerprint, test)
        if duplicates and not request.ignore_duplicate:
            response = WorkflowStatusResponseSchema()
            response.message = "Duplicate request already exists and the following are their response(s)."
            response.duplicates = duplicates
            return response
        workflow = create_new_workflow(db_key, fingerprint, request, test)

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


def create_new_workflow(
        key: str,
        fingerprint: str,
        request: WorkflowRequestSchema,
        test: bool = False,
) -> WorkflowDBSchema:
    """Create a new workflow object and add it to the database"""
    response = WorkflowStatusResponseSchema()
    new_workflow = WorkflowDBSchema(key=key, fingerprint=fingerprint, request=request, response=response)
    workflow = add_workflow(new_workflow, test)
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


def check_for_duplicates(request_hash: str, test: bool = False):
    """
    Check for duplicate workflow request made by a user
      A workflow request is a duplicate request if there exists one or more entries in the DB of similar
      footprint.
    """
    collection = test_collection if test else workflow_collection
    user_responses = []
    workflows = collection.find({"fingerprint": request_hash})
    if workflows:
        for workflow in workflows:
            record = utils.workflow_retrieve_helper(workflow)
            user_response = UserResponseSchema(username=record.request.cube_user_info.username, response=record.response.__dict__)
            user_responses.append(user_response)
        return user_responses


def get_fingerprint(request: WorkflowRequestSchema) -> str:
    """
    Create a unique has on a request footprint.
      A request footprint is a users request payload stripped down to
      include only essential information such as pfdcm_info, workflow_info
      and PACS directive.
    """
    d_data = utils.query_to_dict(request)
    key = utils.dict_to_hash(d_data)
    return key


def get_suproc_params(test: bool, request: WorkflowRequestSchema) -> (str, str):
    """
    Return mode, str_data
    """
    mode = ""
    if test:
        mode = "--test"
    d_data = utils.request_to_dict(request)
    str_data = json.dumps(d_data)
    return mode, str_data
