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


# helpers


def validate_request(request: WorkflowRequestSchema) -> str:
    """
    A helper method validate all required fields in a request payload
    """
    error = ""
    attr_count = 0

    if not request.pfdcm_info.pfdcm_service:
        error += f"\n{Error.required_pfdcm}"

    if not request.pfdcm_info.PACS_service:
        error += f"\n{Error.required_PACS}"

    for k, v in request.PACS_directive:
        if v:
            attr_count += 1

    if attr_count == 0:
        error += f"\n{Error.required_directive}"

    if not request.workflow_info.user_name:
        error += f"\n{Error.required_user}"

    if not request.workflow_info.feed_name:
        error += f"\n{Error.required_feed}"

    if not request.workflow_info.plugin_name:
        error += f"\n{Error.required_plugin}"

    return error


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
    db_key = request_to_hash(request)
    workflow = utils.retrieve_workflow(db_key)
    if not workflow:
        # create a new workflow object
        response = WorkflowStatusResponseSchema()
        # validate request for errors
        error = validate_request(request)
        if error:
            response.status = False
            response.error = error
            return response
        new_workflow = WorkflowDBSchema(key=db_key, request=request, response=response)
        workflow = add_workflow(new_workflow)

    # 'error_type' is an optional test-only parameter that forces the workflow to error out
    # at a given error state
    if error_type:
        return create_response_with_error(error_type, workflow.response)

    mode, str_data = get_suproc_params(test, request)
    # run workflow manager subprocess on the workflow
    sub_mng = manage_workflow(mode, str_data)

    # run status_update subprocess on the workflow
    sub_updt = update_workflow_status(mode, str_data)
    # debug_process(sub_updt)
    return workflow.response


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


def manage_workflow(mode: str, str_data: str):
    """
    Manage a workflow request in a separate subprocess
    """
    subproc = subprocess.Popen(
        ['python',
         'app/controllers/subprocesses/wf_manager.py',
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
         'app/controllers/subprocesses/status.py',
         "--data", str_data,
         "--test", mode,
         ], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    return subproc


def debug_process(bgprocess):
    """
    A blocking method to communicate with a background process and print stdout & stderr
    """
    stderr, stdout = bgprocess.communicate()
    print(stderr, stdout)


def get_suproc_params(test: bool, request: WorkflowRequestSchema) -> (str, str):
    """
    Return mode, str_data
    """
    mode = ""
    if test:
        mode = "testing"
    d_data = utils.query_to_dict(request)
    str_data = json.dumps(d_data)
    return mode, str_data
