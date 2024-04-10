from datetime import datetime

from pymongo import MongoClient, TEXT
import json
import logging
import subprocess
import pprint

from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
    WorkflowDBSchema,
    Error,
    UserResponseSchema,
    State,
    WorkflowSearchSchema,
)
from app.controllers import search
from app.controllers.subprocesses.subprocess_helper import Subprocess
from app.controllers.subprocesses import utils
from app.config import settings

MONGO_DETAILS = str(settings.pflink_mongodb)
client = MongoClient(MONGO_DETAILS, username=settings.mongo_username, password=settings.mongo_password)
database = client.database
workflow_collection = database.get_collection("workflows_collection")
test_collection = database.get_collection("tests_collection")

logger = logging.getLogger('pflink-logger')
d = {'workername': 'PFLINK', 'log_color': "\33[32m", 'key': ""}


# DB methods


# Retrieve all workflows present in the DB

def retrieve_workflows(search_params: WorkflowSearchSchema, test: bool = False):
    collection = test_collection if test else workflow_collection
    index = collection.create_index([('$**', TEXT)],
                                    name='search_index', default_language='english')
    workflows = []
    # query, rank, response = search.compound_queries(search_params)
    workflows = collection.aggregate(
        [
            {"$match": {"$text": {"$search": search_params.keywords}}},
            {"$project": {"_id": 1, "score": {"$meta": "textScore"}}},
            {"$sort": {"score": -1}},
        ]
    )
    search_results = []
    for workflow in workflows:
        search_results.append(str(workflow))

    return search_results


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


async def delete_workflow(workflow_key: str, test: bool = False):
    """
    Delete a workflow record from DB
    """
    collection = test_collection if test else workflow_collection
    resp = collection.delete_one({"_id": workflow_key})
    return {"Message": f"{resp.deleted_count} record(s) deleted!"}


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
    d['key'] = db_key
    workflow = utils.retrieve_workflow(db_key, test)

    mode, str_data = get_suproc_params(test, request)
    if workflow:
        # if there is an existing record in the DB, just run a status subprocess
        sub_updt = update_workflow_status(str_data, mode)

    else:
        fingerprint = get_fingerprint(request)
        duplicates = check_for_duplicates(fingerprint, test)
        if duplicates and not request.ignore_duplicate:
            response = WorkflowStatusResponseSchema()
            response.message = Error.feed_duplicate
            response.workflow_state = State.DUPLICATE_REQUEST
            response.duplicates = duplicates
            return response
        workflow = create_new_workflow(db_key, fingerprint, request, test)

    # 'error_type' is an optional test-only parameter that forces the workflow to error out
    # at a given error state
    if error_type:
        logger.error(workflow.response.error, extra=d)
        return create_response_with_error(error_type, workflow.response)

    # debug_process(sub_updt)

    # run workflow manager subprocess on the workflow
    sub_mng = manage_workflow(str_data, mode)
    logger.info(f"Current status response is {workflow.response.workflow_state}.", extra=d)
    logger.debug(f"Status response is {workflow.response}", extra=d)
    return workflow.response


def create_new_workflow(
        key: str,
        fingerprint: str,
        request: WorkflowRequestSchema,
        test: bool = False,
) -> WorkflowDBSchema:
    """Create a new workflow object and add it to the database"""
    creation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = WorkflowStatusResponseSchema()
    new_workflow = WorkflowDBSchema(key=key,
                                    fingerprint=fingerprint,
                                    creation_time=creation_time,
                                    request=request,
                                    response=response)

    # add new workflow record to DB
    workflow = add_workflow(new_workflow, test)
    pretty_response = pprint.pformat(workflow.response.__dict__)
    logger.info(f"New workflow record created.", extra=d)
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
    except Exception as ex:
        response.error = Error.undefined + f": {ex}"
    return response


def manage_workflow(str_data: str, mode: str):
    """
    Manage a workflow request in a separate subprocess
    """
    workflow_mgr_subprocess = Subprocess("app/controllers/subprocesses/wf_manager.py", str_data)
    proc_count = workflow_mgr_subprocess.get_process_count()
    logger.debug(f"{proc_count} subprocess of workflow manager running on the system.", extra=d)
    if proc_count > 0:
        logger.info(f"No new manager subprocess started.", extra=d)
        return

    d_cmd = ["python", "app/controllers/subprocesses/wf_manager.py", "--data", str_data]
    pretty_cmd = pprint.pformat(d_cmd)
    logger.debug(f"New manager subprocess started with command: {pretty_cmd}", extra=d)
    if mode:
        d_cmd.append(mode)
    subproc = subprocess.Popen(d_cmd)
    return subproc


def update_workflow_status(str_data: str, mode: str):
    """
    Update the current status of a workflow request in a separate process
    """
    status_mgr_subprocess = Subprocess("app/controllers/subprocesses/status.py", str_data)
    proc_count = status_mgr_subprocess.get_process_count()
    logger.debug(f"{proc_count} subprocess of status manager running on the system.", extra=d)
    if proc_count > 0:
        logger.info(f"No new status subprocess started.", extra=d)
        return

    d_cmd = ["python", "app/controllers/subprocesses/status.py", "--data", str_data]
    pretty_cmd = pprint.pformat(d_cmd)
    logger.debug(f"New status subprocess started with command: {pretty_cmd}", extra=d)
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
            user_response = UserResponseSchema(username=record.request.cube_user_info.username,
                                               response=record.response.__dict__)
            user_responses.append(user_response)
        return user_responses


def get_fingerprint(request: WorkflowRequestSchema) -> str:
    """
    Create a unique has on a request fingerprint.
      A request fingerprint is a users request payload stripped down to
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
