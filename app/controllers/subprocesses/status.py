import argparse
import json
import logging
import random
import requests

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
log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

parser = argparse.ArgumentParser(description='Process arguments passed through CLI')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--test', metavar='N', type=str)

args = parser.parse_args()


def update_workflow_status(key: str, test: str):
    """
    Update the status of a workflow object in the DB
    """
    workflow = retrieve_workflow(key)
    # If the status of the workflow is currently being updated by another process
    # or the workflow is in `Completed` state
    # or some error occurred and the workflow status is already marked as false, then do nothing
    if is_status_subprocess_running(workflow) or workflow.response.workflow_state == State.COMPLETED or not workflow.response.status:
        # Do nothing and exit
        return

    logging.info(f"WORKING on updating the status for {key}, locking--")
    update_status_flag(key, workflow, False)

    if test:
        updated_status = get_simulated_status(workflow)
    else:
        updated_status = get_current_status(workflow.request)

    workflow.response = updated_status
    update_status_flag(key, workflow, True)
    logging.info(f"UPDATED status for {key}, releasing lock")


def is_status_subprocess_running(workflow: WorkflowDBSchema):
    proc_count = get_process_count("status",args.data)

    if not workflow.stale and proc_count>0:
        return True
    return False


def update_status_flag(key: str, workflow: WorkflowDBSchema, flag: bool):
    """
    Change the flag `stale` of a workflow response in the DB
    `stale` essentially means the current status information of a workflow is outdated and a new
    `status-update` process can update the information in the DB
    """
    workflow.stale = flag
    update_workflow(key, workflow)


def get_current_status(
        request: WorkflowRequestSchema,
) -> WorkflowStatusResponseSchema:
    """
    Return the status of a workflow in `pflink` by asking `pfdcm` & `cube`. The sequence is as follows:
        1) Ask `pfdcm` about the status of a study
        2) Ask `cube` about the status of the feed created using the study
        3) Parse both the results to a response schema
        4) Return the response
    """
    pfdcm_resp = _get_pfdcm_status(request)
    cube_resp = _get_feed_status(request)
    status = _parse_response(pfdcm_resp, cube_resp)
    return status


def _get_pfdcm_status(request: WorkflowRequestSchema):
    """
    Get the status of PACS from `pfdcm`
    by running the synchronous API of `pfdcm`
    """
    try:
        pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
        pfdcm_status_url = f'{pfdcm_url}/api/v1/PACS/sync/pypx/'
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
        response = requests.post(pfdcm_status_url, json=pfdcm_body, headers=headers)
        return json.loads(response.text)
    except Exception as ex:
        return {"error": Error.pfdcm.value + str(ex)}


def _get_feed_status(request: WorkflowRequestSchema) -> dict:
    """
    Get the status of a feed inside `CUBE`
    1) Create/get a cube client using user_name
    2) Fetch feed details using the client
    3) Serialize for information
    4) Return a suitable response
    """
    try:
        pfdcm_url = retrieve_pfdcm_url(request.pfdcm_info.pfdcm_service)
        cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

        # create a client using the username
        cl = do_cube_create_user(cube_url, request.workflow_info.user_name)

        # substitute dicom values for dicom tags present in feed name
        requested_feed_name = request.workflow_info.feed_name
        pacs_details = cl.getPACSdetails(request.PACS_directive.__dict__)
        feed_name = substitute_dicom_tags(requested_feed_name, pacs_details)

        # search for feed
        resp = cl.getFeed({"name_exact": feed_name})
        return resp
    except Exception as ex:
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
        feed_progress = round((finished / MAX_JOBS) * 100)
        analysis_details['progress'] = str(feed_progress) + "%"

        if errored > 0 or cancelled > 0:
            analysis_details["error"] = str(errored + cancelled) + " job(s) failed"
        if feed_progress == 100:
            analysis_details["state"] = State.COMPLETED
        else:
            analysis_details["state"] = State.ANALYZING

    return analysis_details


def _parse_response(
        pfdcm_response: dict,
        cube_response: dict,
) -> WorkflowStatusResponseSchema:
    """
    Parse JSON object for workflow status response
    """
    status = WorkflowStatusResponseSchema()
    pfdcm_has_error = pfdcm_response.get("error")
    cube_has_error = cube_response.get("error")
    if pfdcm_has_error:
        status.status = False
        status.error = pfdcm_response["error"]
        return status
    valid = pfdcm_response.get('pypx')
    if not valid:
        status.status = False
        status.error = Error.PACS.value + pfdcm_response['message']
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
    update_workflow_status(wf_key, args.test)
