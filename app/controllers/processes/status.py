import argparse
import json
import logging
import random
import requests

from workflow import (
    State,
    WorkflowRequestSchema,
    WorkflowDBSchema,
    WorkflowStatusResponseSchema,
    Error,
)
from utils import (
    dict_to_query,
    query_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
    get_cube_url_from_pfdcm,
    substitute_dicom_tags,
    _do_cube_create_user,
)

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

parser = argparse.ArgumentParser(description='Process arguments passed through CLI')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--test', metavar='N', type=str)
parser.add_argument('--url', metavar='N', type=str)

args = parser.parse_args()

    
def update_workflow_status(key: str, test: str, url: str):
    """
    Update the status of a workflow object in the DB
    """
    workflow = retrieve_workflow(key)
    if not workflow.stale or workflow.response.workflow_state == State.COMPLETED.value:
        # Do nothing and exit
        return
         
    logging.info(f"WORKING on updating the status for {key}, locking--")       
    workflow.stale = False
    update_workflow(key, workflow)

    if test:
        updated_status = get_simulated_status(workflow)
    else:
        updated_status = get_current_status(url, workflow.request)
    
    workflow.response = updated_status
    workflow.stale = True
    update_workflow(key, workflow)
    logging.info(f"UPDATED status for {key}, releasing lock")


def get_current_status(
    pfdcm_url: str,
    request: WorkflowRequestSchema,
) -> WorkflowStatusResponseSchema:
    """
    Return the status of a workflow in `pflink` by asking `pfdcm` & `cube`. The sequence is as follows:
        1) Ask `pfdcm` about the status of a study
        2) Ask `cube` about the status of the feed created using the study
        3) Parse both the results to a response schema
        4) Return the response
    """
    cube_url = get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)
    pfdcm_resp = _get_pfdcm_status(pfdcm_url, request)
    cube_resp = _get_feed_status(cube_url, request)
    status = _parse_response(pfdcm_resp, cube_resp)
    return status


def _get_pfdcm_status(pfdcm_url: str, request: WorkflowRequestSchema):
    """
    Get the status of PACS from `pfdcm`
    by running the synchronous API of `pfdcm`
    """
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


def _get_feed_status(cube_url: str, request: WorkflowRequestSchema):
    """
    Get the status of a feed inside `CUBE`
    1) Create/get a cube client using user_name
    2) Fetch feed details using the client
    3) Serialize for information
    4) Return a suitable response
    """
    MAX_JOBS = 12

    response = WorkflowStatusResponseSchema()
      
    try:     
        cl = _do_cube_create_user(cube_url, request.workflow_info.user_name)
    except Exception as ex:
        response.status = False
        response.error = Error.user.value + str(ex)
        return response

    requested_feed_name = request.workflow_info.feed_name
    pacs_details = cl.getPACSdetails(request.PACS_directive)
    feed_name = substitute_dicom_tags(requested_feed_name, pacs_details)


    try:    
        resp = cl.getFeed({"name_exact": feed_name})
    except Exception as ex:
        response.error = Error.feed.value + str(ex)
        response.status = False
        return response

    if resp['total'] > 0:
        response.workflow_state = State.FEED_CREATED.value
        response.feed_name = resp['data'][0]['name']
        response.feed_id = resp['data'][0]['id']
        response.state_progress = "100%"
        
        # total jobs in the feed
        created = resp['data'][0]['created_jobs']
        waiting = resp['data'][0]['waiting_jobs']
        scheduled = resp['data'][0]['scheduled_jobs']
        started = resp['data'][0]['started_jobs']
        registering = resp['data'][0]['registering_jobs']
        finished = resp['data'][0]['finished_jobs']
        errored = resp['data'][0]['errored_jobs']
        cancelled = resp['data'][0]['cancelled_jobs']
        
        total = created + waiting + scheduled + started + registering + finished + errored + cancelled

        if total > 1:
            response.workflow_state = State.ANALYZING.value
            feed_progress = round((finished/MAX_JOBS) * 100)
            response.state_progress = str(feed_progress) + "%"
            
            if errored > 0 or cancelled > 0:
                response.error = str(errored + cancelled) + " job(s) failed"
            else:
                if feed_progress == 100:
                    response.workflow_state = State.COMPLETED.value

    return response
    
    
def _parse_response(
    pfdcm_response : dict, 
    cube_response  : WorkflowStatusResponseSchema,
) -> WorkflowStatusResponseSchema:
    """
    Parse JSON object for workflow status response
    """
    status = WorkflowStatusResponseSchema()
    valid = pfdcm_response.get('pypx')
    if not valid:
        status.status = False
        status.error = Error.PACS.value +  pfdcm_response['message']
        return status
    data = pfdcm_response['pypx']['data']
    study = pfdcm_response['pypx']['then']['00-status']['study']
    
    if study:
        images = study[0][data[0]['StudyInstanceUID']['value']][0]['images']
        total_images        = images["requested"]["count"]
        total_retrieved     = images["packed"]["count"]
        total_pushed        = images["pushed"]["count"]
        total_registered    = images["registered"]["count"]
        
        if total_images>0:       
            total_ret_perc  = round((total_retrieved/total_images)*100)
            total_push_perc     = round((total_pushed/total_images)*100)
            total_reg_perc = round((total_registered/total_images)*100)       
                  
            if total_ret_perc > 0:
                status.workflow_state = State.RETRIEVING.value
                status.state_progress = str(total_ret_perc) + "%"
            if total_push_perc > 0:
                status.workflow_state = State.PUSHING.value
                status.state_progress = str(total_push_perc) + "%"
            if total_reg_perc > 0:
                status.workflow_state = State.REGISTERING.value
                status.state_progress = str(total_reg_perc) + "%"
    else:
        status.error = Error.study.value
        status.status = False
    if cube_response.feed_id:
        status.feed_name = cube_response.feed_name
        status.feed_id = cube_response.feed_id
        status.workflow_state = cube_response.workflow_state
        status.state_progress = cube_response.state_progress

    return status


def get_simulated_status(workflow: WorkflowDBSchema) -> WorkflowStatusResponseSchema:
    """
    Run a simulation of workflow progress and return an updated status
    """
    MAX_N = 9999
    PROGRESS_JUMP = 25
    current_status = workflow.response
        
    match current_status.workflow_state:
    
        case State.INITIALIZING.value:
            current_status.workflow_state = State.RETRIEVING.value
            current_status.state_progress = "25%"
         
        case State.RETRIEVING.value:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:                
                current_status.workflow_state = State.PUSHING.value
                current_status.state_progress = '25%'
            else:                     
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'
                 
        case State.PUSHING.value:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:              
                current_status.workflow_state = State.REGISTERING.value
                current_status.state_progress = '25%'
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'

        case State.REGISTERING.value:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:             
                current_status.workflow_state = State.FEED_CREATED.value
                current_status.state_progress = '100%'
                current_status.feed_id = random.randint(0, MAX_N)
                d_directive = query_to_dict(workflow.request)['PACS_directive']
                current_status.feed_name = substitute_dicom_tags(workflow.request.workflow_info.feed_name, d_directive)
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'

        case State.FEED_CREATED.value:
            current_status.workflow_state = State.ANALYZING.value
            current_status.state_progress = '25%'

        case State.ANALYZING.value:
            progress = __get_progress_from_text(current_status.state_progress)
            if progress >= 100:                
                current_status.workflow_state = State.COMPLETED.value
            else:
                progress += PROGRESS_JUMP
                current_status.state_progress = str(progress) + '%'
               
    return current_status


def __get_progress_from_text(progress:str):
    """
    Convert progress percentage defined in text to integer
    """
    progress = progress.replace('%','')
    return int(progress)

    
if __name__ == "__main__":
    """
    Main entry point
    """
    dict_data = json.loads(args.data)
    wf_data = dict_to_query(dict_data)
    wf_key = dict_to_hash(dict_data)
    update_workflow_status(wf_key, args.test, args.url)

