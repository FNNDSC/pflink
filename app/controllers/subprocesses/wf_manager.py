"""
This module manages different states of a workflow by constantly checking the status of a workflow in the DB.
"""
import argparse
import json
import logging
import subprocess
import time
import requests
import pprint
from app.controllers.subprocesses.python_chris_client import PythonChrisClient
from app.controllers.subprocesses.subprocess_helper import get_process_count
from logging.config import dictConfig
from app import log
from app.models.workflow import (
    Error,
    State,
    WorkflowRequestSchema,
)
from app.controllers.subprocesses.utils import (
    request_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
    get_cube_url_from_pfdcm,
    substitute_dicom_tags,
    do_cube_create_user,
    retrieve_pfdcm_url,
)
dictConfig(log.log_config)
logger = logging.getLogger('pflink-logger')
d = {'workername': 'WORKFLOW_MGR', 'key' : "",'log_color': "\33[33m"}

parser = argparse.ArgumentParser(description='Process arguments')
parser.add_argument('--data', type=str)
parser.add_argument('--test', default=False, action='store_true')
args = parser.parse_args()


def manage_workflow(db_key: str, test: bool):
    """
    Manage workflow:
    Schedule task based on status from the DB
    """
    SLEEP_TIME = 10
    MAX_RETRIES = 50
    pl_inst_id = 0
    workflow = retrieve_workflow(db_key)
    if workflow.started or not workflow.response.status or test:
        # Do nothing and return
        reason = f"Workflow request failed. {workflow.response.error}" if not workflow.response.status \
                 else f"Workflow already started. The current status is {workflow.response.workflow_state}"
        logger.warning(f"Cannot restart this workflow request. {reason}"
                       f". Kindly delete this request to restart using the delete API end point", extra=d)
        return

    request = workflow.request

    pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
    cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

    while not workflow.response.workflow_state == State.ANALYZING and MAX_RETRIES > 0 and workflow.response.status:

        workflow.started = True
        update_workflow(key, workflow)
        MAX_RETRIES -= 1
        logger.debug(f"{MAX_RETRIES} iterations left.", extra=d)

        match workflow.response.workflow_state:

            case State.INITIALIZING:
                if workflow.stale:
                    logger.info("Requesting PACS retrieve.", extra=d)
                    do_pfdcm_retrieve(request, pfdcm_url)

            case State.RETRIEVING:
                if workflow.response.state_progress == "100%" and workflow.stale:
                    logger.info("Requesting PACS push.", extra=d)
                    do_pfdcm_push(request, pfdcm_url)

            case State.PUSHING:
                if workflow.response.state_progress == "100%" and workflow.stale:
                    logger.info("Requesting PACS register.", extra=d)
                    do_pfdcm_register(request, pfdcm_url)

            case State.REGISTERING:
                if workflow.response.state_progress == "100%" and workflow.stale:
                    try:
                        resp = do_cube_create_feed(request, cube_url)
                        pl_inst_id = resp["pl_inst_id"]
                        feed_id = resp["feed_id"]
                        workflow.response.feed_id = feed_id
                        update_workflow(key, workflow)
                    except Exception as ex:
                        logger.error(Error.feed.value, extra=d)
                        workflow.response.error = Error.feed.value + str(ex)
                        workflow.response.status = False
                        update_workflow(key, workflow)

            case State.FEED_CREATED:
                if workflow.stale:
                    try:
                        do_cube_start_analysis(pl_inst_id, request, cube_url)
                    except Exception as ex:
                        logger.error(Error.analysis.value + str(ex), extra=d)
                        workflow.response.error = Error.analysis.value + str(ex)
                        workflow.response.status = False
                        update_workflow(key, workflow)

        logger.info(f"Calling status update subprocess.", extra=d)
        update_status(request)

        logger.info(f"Sleeping for {SLEEP_TIME} seconds", extra=d)
        time.sleep(SLEEP_TIME)

        workflow = retrieve_workflow(key)
        logger.debug(f"Fetching request status from DB. Current status is {workflow.response.workflow_state}",
                     extra=d)

        # Reset workflow status if max service_retry is not reached
        if workflow.service_retry > 0 and not workflow.response.status:
            logger.warning(f"Retrying request.{workflow.service_retry}/5 retries left.", extra=d)
            workflow.service_retry -= 1
            workflow.response.error = ""
            workflow.response.status = True
            update_workflow(key, workflow)


        # Reset workflow if pflink reached MAX no. of retries
        if MAX_RETRIES==0:
            logger.debug(f"Maximum retry limit reached. Resetting request flag to NOT STARTED.", extra=d)
            workflow.started = False
            update_workflow(key, workflow)
            logger.info("Exiting manager subprocess", extra=d)

    logger.info(f"Exiting while loop. End of workflow_manager.", extra=d)


def update_status(request: WorkflowRequestSchema):
    """
    Trigger an update status in 
    a separate python process
    """
    d_data = request_to_dict(request)
    str_data = json.dumps(d_data)
    proc_count = get_process_count("status", str_data)
    logger.debug(f"{proc_count} subprocess of status manager running on the system.", extra=d)
    if proc_count > 0:
        logger.info(f"No new status subprocess started.", extra=d)
        return
    d_cmd = ["python", "app/controllers/subprocesses/status.py", "--data", str_data]
    pretty_cmd = pprint.pformat(d_cmd)
    logger.debug(f"New status subprocess started with command: {pretty_cmd}", extra=d)
    process = subprocess.Popen(d_cmd)


def pfdcm_do(verb: str, then_args: dict, request: WorkflowRequestSchema, url: str):
    """
    A reusable method to either retrieve, push or register dicoms using pfdcm
    by running the threaded API of `pfdcm`
    """
    then_args = json.dumps(then_args, separators=(',', ':'))
    pfdcm_dicom_api = f'{url}/PACS/thread/pypx/'
    headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
    body = {
        "PACSservice": {
            "value": request.pfdcm_info.PACS_service
        },
        "listenerService": {
            "value": "default"
        },
        "PACSdirective": {
            "AccessionNumber": request.PACS_directive.AccessionNumber,
            "PatientID": request.PACS_directive.PatientID,
            "PatientName": request.PACS_directive.PatientName,
            "PatientBirthDate": request.PACS_directive.PatientBirthDate,
            "PatientAge": request.PACS_directive.PatientAge,
            "PatientSex": request.PACS_directive.PatientSex,
            "StudyDate": request.PACS_directive.StudyDate,
            "StudyDescription": request.PACS_directive.StudyDescription,
            "StudyInstanceUID": request.PACS_directive.StudyInstanceUID,
            "Modality": request.PACS_directive.Modality,
            "ModalitiesInStudy": request.PACS_directive.ModalitiesInStudy,
            "PerformedStationAETitle": request.PACS_directive.PerformedStationAETitle,
            "NumberOfSeriesRelatedInstances": request.PACS_directive.NumberOfSeriesRelatedInstances,
            "InstanceNumber": request.PACS_directive.InstanceNumber,
            "SeriesDate": request.PACS_directive.SeriesDate,
            "SeriesDescription": request.PACS_directive.SeriesDescription,
            "SeriesInstanceUID": request.PACS_directive.SeriesInstanceUID,
            "ProtocolName": request.PACS_directive.ProtocolName,
            "AcquisitionProtocolDescription": request.PACS_directive.AcquisitionProtocolDescription,
            "AcquisitionProtocolName": request.PACS_directive.AcquisitionProtocolName,
            "withFeedBack": True,
            "then": verb,
            "thenArgs": then_args,
            "dblogbasepath": '/home/dicom/log',
            "json_response": False
        }
    }
    pretty_json = pprint.pformat(body)
    logger.debug(f"POSTing the below request at {pfdcm_dicom_api} to {verb}: {pretty_json}", extra=d)
    st = time.time()
    response = requests.post(pfdcm_dicom_api, json=body, headers=headers)
    et = time.time()
    elapsed_time = et - st
    logger.debug(f'Execution time to request {verb}:{elapsed_time} seconds', extra=d)


def do_pfdcm_retrieve(dicom: WorkflowRequestSchema, pfdcm_url: str):
    """
    Retrieve PACS using pfdcm
    """
    retrieve_args = {}
    pfdcm_do("retrieve", retrieve_args, dicom, pfdcm_url)


def do_pfdcm_push(request: WorkflowRequestSchema, pfdcm_url: str):
    """
    Push PACS to a Swift store using `pfdcm`
    """
    push_args = {
        'db': request.pfdcm_info.db_log_path,
        'swift': request.pfdcm_info.swift_service,
        'swiftServicesPACS': request.pfdcm_info.PACS_service,
        'swiftPackEachDICOM': True
    }
    pfdcm_do("push", push_args, request, pfdcm_url)


def do_pfdcm_register(request: WorkflowRequestSchema, pfdcm_url: str):
    """
    Register PACS files to a `CUBE`
    """
    register_args = {
        "db": request.pfdcm_info.db_log_path,
        "CUBE": request.pfdcm_info.cube_service,
        "swiftServicesPACS": request.pfdcm_info.PACS_service,
        "parseAllFilesWithSubStr": request.pfdcm_info.dicom_file_extension
    }
    pfdcm_do("register", register_args, request, pfdcm_url)


def do_cube_create_feed(request: WorkflowRequestSchema, cube_url: str) -> dict:
    """
    Create a new feed in `CUBE` if not already present
    """
    client = do_cube_create_user(cube_url, request.cube_user_info.username, request.cube_user_info.password)
    pacs_details = client.getPACSdetails(request.PACS_directive.__dict__)
    feed_name = substitute_dicom_tags(request.workflow_info.feed_name, pacs_details)
    data_path = client.getSwiftPath(pacs_details)

    # Get plugin Id
    plugin_search_params = {"name": "pl-dircopy"}
    plugin_id = client.getPluginId(plugin_search_params)

    logger.info(f"Creating a new feed with feed name: {feed_name}", extra=d)
    # create a feed
    feed_params = {'title': feed_name, 'dir': data_path}
    feed_response = client.createFeed(plugin_id, feed_params)
    return {"feed_id": feed_response["feed_id"], "pl_inst_id": feed_response["id"]}


def do_cube_start_analysis(previous_id: str, request: WorkflowRequestSchema, cube_url: str):
    """
    Create a new node (plugin instance) on an existing feed in `CUBE`
    """
    client = do_cube_create_user(cube_url, request.cube_user_info.username, request.cube_user_info.password)
    if request.workflow_info.plugin_name:
        __run_plugin_instance(previous_id, request, client)
    if request.workflow_info.pipeline_name:
        __run_pipeline_instance(previous_id,request, client)


def __run_plugin_instance(previous_id: str, request: WorkflowRequestSchema, client: PythonChrisClient):
    """
    Run a plugin instance on an existing (previous) plugin instance ID in CUBE
    """
    # search for plugin
    plugin_search_params = {"name": request.workflow_info.plugin_name, "version": request.workflow_info.plugin_version}
    plugin_id = client.getPluginId(plugin_search_params)

    # convert CLI params from string to a JSON dictionary
    feed_params = str_to_param_dict(request.workflow_info.plugin_params)
    feed_params["previous_id"] = previous_id
    logger.debug(f"Creating new analysis with plugin: {plugin_search_params}  and parameters: {feed_params}",
                 extra=d)
    feed_resp = client.createFeed(plugin_id, feed_params)


def __run_pipeline_instance(previous_id: str, request: WorkflowRequestSchema, client: PythonChrisClient):
    """
    Run a workflow instance on an existing (previous) plugin instance ID in CUBE
    """
    # search for pipeline
    pipeline_search_params = {"name": request.workflow_info.pipeline_name}
    pipeline_id = client.getPipelineId(pipeline_search_params)
    pipeline_params = {"previous_plugin_inst_id": previous_id, "name": request.workflow_info.pipeline_name}
    feed_resp = client.createWorkflow(str(pipeline_id), pipeline_params)


def str_to_param_dict(params: str) -> dict:
    """
    Convert CLI arguments passed as string to a dictionary of parameters
    """
    d_params = {}
    params_text = params.strip()
    params_dict = params_text.split('--')

    for param in params_dict:
        if param == "":
            continue
        param = param.strip()
        items = param.split(' ',1)
        if len(items)==1:
            d_params[items[0]] = True
        else:
            d_params[items[0]] = items[1]


    return d_params


if __name__ == "__main__":
    """
    Main entry point of this script
    """
    d_data = json.loads(args.data)
    key = dict_to_hash(d_data)
    d['key'] = key
    manage_workflow(key, args.test)

