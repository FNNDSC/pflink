"""
This module updates the state of a workflow in the DB
"""
import argparse
import json
import logging
import random
import requests
import time
import pprint
from logging.config import dictConfig
from app.models.log import LogConfig
from app.log_config import log_config
from app.models.workflow import (
    State,
    WorkflowRequestSchema,
    WorkflowDBSchema,
    WorkflowStatusResponseSchema,
    Error,
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

from app.controllers.subprocesses.subprocess_helper import get_process_count
dictConfig(log_config)
logger = logging.getLogger('pflink-logger')
d = {'workername': 'STATUS_MGR', 'log_color': "\33[36m", 'key': ""}


parser = argparse.ArgumentParser(description='Process arguments passed through CLI')
parser.add_argument('--data', type=str)
parser.add_argument('--test', default=False, action='store_true')

args = parser.parse_args()


def update_workflow_status(key: str, test: bool):
    """
    Update the status of a workflow object in the DB
    """
    workflow = retrieve_workflow(key, test)
    # If the status of the workflow is currently being updated by another process
    # Do nothing and exit
    if is_status_subprocess_running(workflow):
        return

    logger.info(f"Working on fetching the current status, locking DB flag", extra=d)
    update_status_flag(key, workflow, False, test)

    if test:
        updated_status = get_simulated_status(workflow)
    else:
        updated_status = get_current_status(workflow.request, workflow.response)

    workflow.response = update_workflow_progress(updated_status)
    pretty_response = pprint.pformat(workflow.response.__dict__)
    logger.debug(f"Updated response: {pretty_response}", extra=d)
    update_status_flag(key, workflow, True, test)
    logger.info(f"Finished writing updated status to the DB, releasing lock", extra=d)


def update_workflow_progress(response: WorkflowStatusResponseSchema):
    """
    Update the overall workflow progress of a workflow from its current
    workflow state.
    """
    MAX_STATE = 7
    index = 0
    for elem in State:
        if response.workflow_state == elem:
            state_progress = int(response.state_progress.replace('%',''))

            response.workflow_progress_perc = max(response.workflow_progress_perc,
                                                  __progress_percent(index,MAX_STATE,state_progress))
        index += 1
    return response


def __progress_percent(curr_state: int, total_states: int, state_progress: int) -> int:
    """
    Return the percentage of states completed when the total no. of states and
    current state is given.

    """
    progress_percent = round((curr_state/total_states) * 100 + (state_progress/total_states))
    return  progress_percent


def is_status_subprocess_running(workflow: WorkflowDBSchema):
    proc_count = get_process_count("status", args.data)

    if not workflow.stale:
        return True
    return False


def update_status_flag(key: str, workflow: WorkflowDBSchema, flag: bool, test: bool):
    """
    Change the flag `stale` of a workflow response in the DB
    `stale` essentially means the current status information of a workflow is outdated and a new
    `status-update` process can update the information in the DB
    """
    workflow.stale = flag
    update_workflow(key, workflow, test)


def get_current_status(
        request: WorkflowRequestSchema,
        status: WorkflowStatusResponseSchema,
) -> WorkflowStatusResponseSchema:
    """
    Return the status of a workflow in `pflink` by asking `pfdcm` & `cube`. The sequence is as follows:
        1) Ask `pfdcm` about the status of a study
        2) Ask `cube` about the status of the feed created using the study
        3) Serialize both the results to a response schema
        4) Return the response
    """
    pfdcm_resp = _get_pfdcm_status(request)
    cube_resp = _get_feed_status(request, status.feed_id)
    status = _parse_response(pfdcm_resp, cube_resp, status)
    return status


def _get_pfdcm_status(request: WorkflowRequestSchema):
    """
    Get the status of PACS from `pfdcm`
    by running the synchronous API of `pfdcm`
    """
    try:
        pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
        pfdcm_status_url = f'{pfdcm_url}/PACS/sync/pypx/'
        headers = {'Content-Type': 'application/json', 'accept': 'application/json'}

        pfdcm_body = {
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
                "then": 'status',
                "thenArgs": "",
                "dblogbasepath": request.pfdcm_info.db_log_path,
                "json_response": True
            }
        }
        pretty_json = pprint.pformat(pfdcm_body)
        logger.debug(f"POSTing the below request at {pfdcm_status_url} to get status: {pretty_json}", extra=d)
        st = time.time()
        response = requests.post(pfdcm_status_url, json=pfdcm_body, headers=headers)
        et = time.time()
        elapsed_time = et - st
        logger.debug(f'Execution time to get status:{elapsed_time} seconds', extra=d)
        d_response = json.loads(response.text)
        #logger.debug(f"Response from pfdcm: {d_response}")
        d_response["service_name"] = request.pfdcm_info.pfdcm_service
        return d_response
    except Exception as ex:
        logger.error(f"{Error.pfdcm.value}  {str(ex)} for pfdcm_service {request.pfdcm_info.pfdcm_service}", extra=d)
        return {"error": Error.pfdcm.value + f" {str(ex)} for pfdcm_service {request.pfdcm_info.pfdcm_service}"}


def _get_feed_status(request: WorkflowRequestSchema, feed_id: str) -> dict:
    """
    Get the status of a feed inside `CUBE`
    1) Create/get a cube client using user_name
    2) Fetch feed details using the client
    3) Serialize for information
    4) Return a suitable response
    """
    if feed_id == "":
        return {}
    try:
        pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
        cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

        # create a client using the username
        cl = do_cube_create_user(cube_url, request.cube_user_info.username, request.cube_user_info.password)

        # substitute dicom values for dicom tags present in feed name
        requested_feed_name = request.workflow_info.feed_name
        pacs_details = cl.getPACSdetails(request.PACS_directive.__dict__)
        feed_name = substitute_dicom_tags(requested_feed_name, pacs_details)

        # search for feed
        logger.debug(f"Request CUBE at {cube_url} for feed id: {feed_id} and feed name: {feed_name}", extra=d)
        resp = cl.getFeed({"id": feed_id, "name_exact": feed_name})
        pretty_response = pprint.pformat(resp)
        logger.debug(f"Response from CUBE : {pretty_response}", extra=d)
        if resp["errored_jobs"] or resp["cancelled_jobs"]:
            l_inst_resp = cl.getPluginInstances({"feed_id": feed_id})
            l_error = [d_instance['plugin_name'] for d_instance in l_inst_resp['data'] if d_instance['status']=='finishedWithError' or d_instance['status'] == 'cancelled']
            resp["errored_plugins"] = str(l_error)
        return resp
    except Exception as ex:
        logger.error(f"{Error.cube.value} {str(ex)}", extra=d)
        return {"error": Error.cube.value + str(ex)}


def get_analysis_status(response: dict) -> dict:
    """
    Get details about an analysis running on the given feed
    """
    MAX_JOBS = 12
    analysis_details = {}

    created = response['created_jobs']
    waiting = response['waiting_jobs']
    scheduled = response['scheduled_jobs']
    started = response['started_jobs']
    registering = response['registering_jobs']
    finished = response['finished_jobs']
    errored = response['errored_jobs']
    cancelled = response['cancelled_jobs']

    total = created + waiting + scheduled + started + registering + finished + errored + cancelled

    if total > 1:
        feed_progress = round((finished / total) * 100)
        analysis_details['progress'] = str(feed_progress) + "%"

        if errored > 0 or cancelled > 0:
            analysis_details["error"] = f"{(errored + cancelled)} job(s) failed : {response['errored_plugins']}"
        if feed_progress == 100:
            analysis_details["state"] = State.COMPLETED
        else:
            analysis_details["state"] = State.ANALYZING

    return analysis_details


def _parse_response(
        pfdcm_response: dict,
        cube_response: dict,
        status: WorkflowStatusResponseSchema,
) -> WorkflowStatusResponseSchema:
    """
    Parse JSON object for workflow status response
    """
    # status = WorkflowStatusResponseSchema()
    pfdcm_has_error = pfdcm_response.get("error")
    cube_has_error = cube_response.get("error")
    if pfdcm_has_error:
        status.status = False
        status.error = pfdcm_response["error"]
        return status
    valid = pfdcm_response.get('pypx')
    if not valid:
        status.status = False
        status.error = Error.PACS.value + f" {pfdcm_response['message']} for pfdcm_service" \
                                          f" {pfdcm_response['service_name']}"
        return status
    data = pfdcm_response['pypx']['data']
    study = pfdcm_response['pypx']['then']['00-status']['study']

    if study:
        images = study[0][data[0]['StudyInstanceUID']['value']][0]['images']
        total_images = images["requested"]["count"]
        total_retrieved = images["packed"]["count"]
        total_pushed = images["pushed"]["count"]
        total_registered = images["registered"]["count"]

        if total_images > 0:
            total_ret_perc = round((total_retrieved / total_images) * 100)
            total_push_perc = round((total_pushed / total_images) * 100)
            total_reg_perc = round((total_registered / total_images) * 100)

            if total_ret_perc > 0:
                status.workflow_state = State.RETRIEVING
                status.state_progress = str(total_ret_perc) + "%"
            if total_push_perc > 0:
                status.workflow_state = State.PUSHING
                status.state_progress = str(total_push_perc) + "%"
            if total_reg_perc > 0:
                status.workflow_state = State.REGISTERING
                status.state_progress = str(total_reg_perc) + "%"
    else:
        status.error = Error.study.value
        status.status = False
        return status

    if cube_has_error:
        status.status = False
        status.error = cube_response["error"]
        return status

    if cube_response:
        status.workflow_state = State.FEED_CREATED
        status.feed_name = cube_response['name']
        status.feed_id = cube_response['id']
        status.state_progress = "100%"

        # check if analysis is scheduled
        analysis = get_analysis_status(cube_response)
        if analysis:
            analysis_has_error = analysis.get("error")
            status.workflow_state = analysis["state"]
            status.state_progress = analysis["progress"]
            if analysis_has_error:
                status.error = analysis["error"]
                status.status = False
                return status

    else:
        if status.feed_name:
            status.workflow_state = State.FEED_DELETED
            status.status = False
            status.error = Error.feed_deleted.value

    return status


def get_simulated_status(workflow: WorkflowDBSchema) -> WorkflowStatusResponseSchema:
    """
    Run a simulation of workflow progress and return an updated status
    """
    MAX_N = 9999
    PROGRESS_JUMP = 25
    current_status = workflow.response

    match current_status.workflow_state:

        case State.INITIALIZING:
            current_status.workflow_state = State.RETRIEVING
            current_status.state_progress = "25%"

        case State.RETRIEVING:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:
                current_status.workflow_state = State.PUSHING
                current_status.state_progress = '25%'
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'

        case State.PUSHING:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:
                current_status.workflow_state = State.REGISTERING
                current_status.state_progress = '25%'
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'

        case State.REGISTERING:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:
                current_status.workflow_state = State.FEED_CREATED
                current_status.state_progress = '100%'
                current_status.feed_id = random.randint(0, MAX_N)
                d_directive = query_to_dict(workflow.request)['PACS_directive']
                current_status.feed_name = substitute_dicom_tags(workflow.request.workflow_info.feed_name, d_directive)
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'

        case State.FEED_CREATED:
            current_status.workflow_state = State.ANALYZING
            current_status.state_progress = '25%'

        case State.ANALYZING:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:
                current_status.workflow_state = State.COMPLETED
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'

    return current_status


def __get_progress_from_text(progress: str):
    """
    Convert progress percentage defined in text to integer
    """
    progress = progress.replace('%', '')
    return int(progress)


if __name__ == "__main__":
    """
    Main entry point
    """
    dict_data = json.loads(args.data)
    wf_key = dict_to_hash(dict_data)
    d['key'] = wf_key
    update_workflow_status(wf_key, args.test)
