import argparse
import json
import logging
import subprocess
import time
import requests
from app.models.workflow import (
    Error,
    State,
    WorkflowRequestSchema,
    WorkflowInfoSchema,
)
from app.controllers.subprocesses.utils import (
    query_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
    get_cube_url_from_pfdcm,
    substitute_dicom_tags,
    do_cube_create_user,
    retrieve_pfdcm_url,
)

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

parser = argparse.ArgumentParser(description='Process arguments')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--test', metavar='N', type=str)
args = parser.parse_args()


def manage_workflow(db_key: str, test: str):
    """
    Manage workflow:
    Schedule task based on status 
    from the DB
    """
    MAX_RETRIES = 50
    pl_inst_id = 0
    workflow = retrieve_workflow(db_key)
    if workflow.started or not workflow.response.status or test:
        # Do nothing and return
        return

    request = workflow.request
    pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
    cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

    while not workflow.response.workflow_state == State.FEED_CREATED.value and MAX_RETRIES > 0:
        workflow.started = True
        update_workflow(key, workflow)
        MAX_RETRIES -= 1

        match workflow.response.workflow_state:

            case State.INITIALIZING.value:
                if workflow.stale:
                    do_pfdcm_retrieve(request, pfdcm_url)

            case State.RETRIEVING.value:
                if workflow.response.state_progress == "100%" and workflow.stale:
                    do_pfdcm_push(request, pfdcm_url)

            case State.PUSHING.value:
                if workflow.response.state_progress == "100%" and workflow.stale:
                    do_pfdcm_register(request, pfdcm_url)

            case State.REGISTERING.value:
                if workflow.response.state_progress == "100%" and workflow.stale:
                    try:
                        pl_inst_id = do_cube_create_feed(request, cube_url)
                    except Exception as ex:
                        logging.info(Error.feed.value)
                        workflow.response.error = Error.feed.value + str(ex)
                        workflow.response.status = False
                        update_workflow(key, workflow)
                        break

        update_status(request, test)
        time.sleep(10)
        workflow = retrieve_workflow(key)

    if pl_inst_id == 0:
        return

    try:
        do_cube_start_analysis(pl_inst_id, request.workflow_info, cube_url)
    except Exception as ex:
        logging.info(Error.analysis.value)
        workflow.response.error = Error.analysis.value + str(ex)
        workflow.response.status = False
        update_workflow(key, workflow)


def update_status(request: WorkflowRequestSchema, test: str):
    """
    Trigger an update status in 
    a separate python process
    """
    d_data = query_to_dict(request)
    str_data = json.dumps(d_data)
    process = subprocess.Popen(
        ['python',
         'app/controllers/subprocesses/status.py',
         "--data", str_data,
         "--test", test,
         ], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)


def pfdcm_do(verb: str, then_args: dict, request: WorkflowRequestSchema, url: str):
    """
    A reusable method to either retrieve, push or register dicoms using pfdcm
    by running the threaded API of `pfdcm`
    """
    then_args = json.dumps(then_args, separators=(',', ':'))
    pfdcm_dicom_api = f'{url}/api/v1/PACS/thread/pypx/'
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
    st = time.time()
    response = requests.post(pfdcm_dicom_api, json=body, headers=headers)
    et = time.time()
    elapsed_time = et - st
    logging.info(f'Execution time to {verb}:{elapsed_time} seconds')


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
        'swiftServicesPACS': request.pfdcm_info.swift_service_PACS,
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
        "swiftServicesPACS": request.pfdcm_info.swift_service_PACS,
        "parseAllFilesWithSubStr": request.pfdcm_info.dicom_file_extension
    }
    pfdcm_do("register", register_args, request, pfdcm_url)


def do_cube_create_feed(request: WorkflowRequestSchema, cube_url: str) -> str:
    """
    Create a new feed in `CUBE` if not already present
    """
    client = do_cube_create_user(cube_url, request.workflow_info.user_name)
    pacs_details = client.getPACSdetails(request.PACS_directive.__dict__)
    feed_name = substitute_dicom_tags(request.workflow_info.feed_name, pacs_details)
    data_path = client.getSwiftPath(pacs_details)

    # Get plugin Id
    plugin_search_params = {"name": "pl-dircopy"}
    plugin_id = client.getPluginId(plugin_search_params)

    # create a feed
    feed_params = {'title': feed_name, 'dir': data_path}
    feed_response = client.createFeed(plugin_id, feed_params)
    return feed_response['id']


def do_cube_start_analysis(previous_id: str, workflow_info: WorkflowInfoSchema, cube_url: str):
    """
    Create a new node (plugin instance) on an existing feed in `CUBE`
    """
    client = do_cube_create_user(cube_url, workflow_info.user_name)
    # search for plugin
    plugin_search_params = {"name": workflow_info.plugin_name, "version": workflow_info.plugin_version}
    plugin_id = client.getPluginId(plugin_search_params)

    # convert CLI params from string to a JSON dictionary
    feed_params = str_to_param_dict(workflow_info.plugin_params)
    feed_params["previous_id"] = previous_id
    feed_resp = client.createFeed(plugin_id, feed_params)


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
        items = param.split(' ')
        d_params[items[0]] = items[1]

    return d_params


if __name__ == "__main__":
    """
    Main entry point of this script
    """
    d_data = json.loads(args.data)
    key = dict_to_hash(d_data)
    manage_workflow(key, args.test)

