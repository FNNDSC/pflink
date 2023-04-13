import argparse
import json
import logging
import random
import requests
from client.PythonChrisClient import PythonChrisClient
from workflow import (
    State,
    WorkflowRequestSchema,
    WorkflowDBSchema,
    WorkflowInfoSchema,
    WorkflowStatusResponseSchema,
)
from utils import (
    dict_to_query,
    query_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
)

log_format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    datefmt="%H:%M:%S"
)

parser = argparse.ArgumentParser(description='Process arguments passed through CLI')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--pfdcm_url', metavar='N', type=str)

args = parser.parse_args()

    
def update_workflow_status(
    key: str,
    test: bool,
):
    """
    Update the status of a workflow object
    in the DB
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
        updated_status = get_current_status(workflow.request)
    
    workflow.response = updated_status
    workflow.stale = True
    update_workflow(key, workflow)
    logging.info(f"UPDATED status for {key}, releasing lock")


def get_current_status(
    request: WorkflowRequestSchema,
) -> WorkflowStatusResponseSchema:
    """
    Return the status of a workflow in `pflink`
    by asking `pfdcm` & `cube`. The sequence is as
    follows:
        1) Ask `pfdcm` about the status of a study
        2) Ask `cube` about the status of the feed created using the study
        3) Parse both the results to a response schema
        4) Return the response
    """
    pfdcm_url = get_pfdcm_url(request.pfdcm_info.pfdcm_service)
    cube_url = _get_cube_url_from_pfdcm(pfdcm_url, request.pfdcm_info.cube_service)

    pfdcm_resp = _get_pfdcm_status(pfdcm_url, request)
    cube_resp = _get_feed_status(cube_url, request.workflow_info)
    status = _parse_response(pfdcm_resp, cube_resp,key)
    return status


def _get_cube_url_from_pfdcm(pfdcm_url: str, cube_name: str) -> str:
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cube_name}/'
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text)
    cube_url = d_results['cubeInfo']['url']
    return cube_url


def _get_pfdcm_status(pfdcm_url: str, request: WorkflowRequestSchema):
    """
    Get the status of PACS from `pfdcm`
    by running the synchronous API of `pfdcm`
    """
    pfdcm_status_url = f'{pfdcm_url}/api/v1/PACS/sync/pypx/'
    headers = {'Content-Type': 'application/json', 'accept': 'application/json'}
    
    pfdcm_request = {
        "PACSservice": {
          "value": request.pfdcm_info.pacs_service
        },
        "listenerService": {
          "value": "default"
         },
        "PACSdirective": {
          "AccessionNumber": request.pacs_directive.AccessionNumber,
          "PatientID": request.pacs_directive.PatientID,
          "PatientName": request.pacs_directive.PatientName,
          "PatientBirthDate": request.pacs_directive.PatientBirthDate,
          "PatientAge": request.pacs_directive.PatientAge,
          "PatientSex": request.pacs_directive.PatientSex,
          "StudyDate": request.pacs_directive.StudyDate,
          "StudyDescription": request.pacs_directive.StudyDescription,
          "StudyInstanceUID": request.pacs_directive.StudyInstanceUID,
          "Modality": request.pacs_directive.Modality,
          "ModalitiesInStudy": request.pacs_directive.ModalitiesInStudy,
          "PerformedStationAETitle": request.pacs_directive.PerformedStationAETitle,
          "NumberOfSeriesRelatedInstances": request.pacs_directive.NumberOfSeriesRelatedInstances,
          "InstanceNumber": request.pacs_directive.InstanceNumber,
          "SeriesDate": request.pacs_directive.SeriesDate,
          "SeriesDescription": request.pacs_directive.SeriesDescription,
          "SeriesInstanceUID": request.pacs_directive.SeriesInstanceUID,
          "ProtocolName": request.pacs_directive.ProtocolName,
          "AcquisitionProtocolDescription": request.pacs_directive.AcquisitionProtocolDescription,
          "AcquisitionProtocolName": request.pacs_directive.AcquisitionProtocolName,
          "withFeedBack": True,
          "then": 'status',
          "thenArgs": "",
          "dblogbasepath": request.pfdcm_info.db_log_path,
          "json_response": True
        }
      }

    response = requests.post(
                   pfdcm_status_url, 
                   json=pfdcm_request,
                   headers=headers
               )

    return json.loads(response.text) 


def _get_feed_status(cube_url: str, workflow_info: WorkflowInfoSchema):
    """
    Get the status of a feed inside `CUBE`
    1) Create/get a cube client using user_name
    2) Fetch feed details using the client
    3) Serialize for information
    4) Return a suitable response
    """
    MAX_JOBS = 12
        
    cube_response = {
        "feed_name"       : "",
        "state"      : "",
        "feed_progress"   : "0%",
        "feed_status"     : "",
        "feed_id"      : "",
        "error"         : ""
    }
      
    try:     
        cl = _do_cube_create_user(cube_url, workflow_info.user_name)
    except Exception as ex:
        cube_response['error'] = str(ex)
        return cube_response

    # feed_name = get_feed_name_do_something()

    try:    
        resp = cl.getFeed({"name_exact": feed_name})
    except Exception as ex:
        cube_response["error"] = str(ex)
        return cube_response

    if resp['total']>0:
        cube_response['state'] = State.FEED_CREATED.value
        cube_response['feed_name'] = resp['data'][0]['name']
        cube_response['feed_id'] = resp['data'][0]['id']
        cube_response['feed_progress'] = "100%"
        
        # total jobs in the feed
        created = resp['data'][0]['created_jobs']
        waiting = resp['data'][0]['waiting_jobs']
        scheduled = resp['data'][0]['scheduled_jobs']
        started = resp['data'][0]['started_jobs']
        registering = resp['data'][0]['registering_jobs']
        finished = resp['data'][0]['finished_jobs']
        errored = resp['data'][0]['errored_jobs']
        cancelled = resp['data'][0]['cancelled_jobs']
        
        total = created + waiting + scheduled +started + registering + finished +errored + cancelled

        if total>1:
            cubeResponse['FeedState']     = State.ANALYZING.name
            feedProgress                  = round((finished/MAX_JOBS) * 100)
            cubeResponse['FeedProgress']  = str(feedProgress) + "%"
            feedStatus                    = ""
            
            if errored>0 or cancelled>0:
                cubeResponse['FeedError'] = str(errored + cancelled) + " job(s) failed"
                feedStatus                = "Failed"
            else:
                if feedProgress==100:
                    feedStatus                      = "Complete"
                    cubeResponse['FeedState']       = State.COMPLETED.name
                else:
                    feedStatus = "In progress"
             
            cubeResponse['FeedStatus'] = feedStatus            
            
    return cubeResponse
    
    
def _parse_response(
    pfdcmResponse : dict, 
    cubeResponse  : dict,
    key           : str, 
) -> dict:
    """
    Parse JSON object for workflow status response
    """
    
    status   = retrieve_workflow(key).status
    valid    = pfdcmResponse.get('pypx')
    if not valid:
        status.Status = False
        status.Error = pfdcmResponse['message']
        return status
    data     = pfdcmResponse['pypx']['data']
    study    = pfdcmResponse['pypx']['then']['00-status']['study']
    
    if study:
        #status.WorkflowState = State.RETRIEVING.name
        images             = study[0][data[0]['StudyInstanceUID']['value']][0]['images'] 
        totalImages        = images["requested"]["count"]
        totalRetrieved     = images["packed"]["count"]
        totalPushed        = images["pushed"]["count"]
        totalRegistered    = images["registered"]["count"]
        
        if totalImages>0:       
            totalRetrievedPerc  = round((totalRetrieved/totalImages)*100)
            totalPushedPerc     = round((totalPushed/totalImages)*100)
            totalRegisteredPerc = round((totalRegistered/totalImages)*100)       
                  
            if totalRetrievedPerc > 0:
                status.WorkflowState = State.RETRIEVING.name
                status.StateProgress = str(totalRetrievedPerc) + "%"
            if totalPushedPerc > 0:
                status.WorkflowState = State.PUSHING.name
                status.StateProgress = str(totalPushedPerc) + "%"
            if totalRegisteredPerc > 0:
                status.WorkflowState = State.REGISTERING.name
                status.StateProgress = str(totalRegisteredPerc) + "%"
    else:
        status.Error  = "Study not found in the PACS server. Please enter valid study info."
        status.Status = False
        
    if cubeResponse:           
       if cubeResponse['FeedState'] != "":
            status.WorkflowState   = cubeResponse['FeedState']           
            status.FeedId          = cubeResponse['FeedId']
            status.FeedName        = cubeResponse['FeedName']
            status.StateProgress   = cubeResponse['FeedProgress']
            status.Message         = cubeResponse['FeedStatus']       
            status.Error           = cubeResponse['FeedError']
    return status 


def _do_cube_create_user(cubeUrl,userName):
    """
    Create a new user in `CUBE` if not already present
    """
    createUserUrl    = cubeUrl+"users/"
    userPass         = userName + "1234"
    userEmail        = userName + "@email.com"
    
    # create a new user
    headers     = {
                      'Content-Type': 'application/json',
                      'accept': 'application/json'
                  }
                  
    myobj       = {
                     "username" : userName,
                     "password" : userPass,
                     "email"    : userEmail,
                  }
                  
    resp        = requests.post(
                     createUserUrl,
                     json=myobj,
                     headers=headers
                 )
                             
    authClient = PythonChrisClient(
                     cubeUrl,
                     userName,
                     userPass
                 )
                 
                 
    return authClient

    
def _parse_feed_template(
    feedTemplate : str, 
    dcmData      : dict
) -> str:
    """
    Given a feed name template, substitute dicom values
    for specified dicom tags
    """
    items    = feedTemplate.split('%')
    feedName = ""
    
    for item in items:
        if item == "":
            continue;           
        tags     = item.split('-')
        dicomTag = tags[0]
        
        try:        
            dicomValue = dcmData[dicomTag]["value"]
        except:
            dicomValue = dicomTag
            
        item     = item.replace(dicomTag,dicomValue)
        feedName = feedName + item

    return feedName 


def substitute_dicom_tags(
    text: str,
    dicom_data: dict
) -> str:
    """
    # Given a string containing dicom tags separated by `%`, substitute dicom values
    # for those dicom tags from a given dictionary if present
    """
    text_w_values = ""
    items = text.split('%')
    for item in items:
        if item == "":
            continue
            
        tags = item.split('-')
        dicom_tag = tags[0]
        
        try:        
            dicom_value = dicom_data[dicom_tag]
        except:
            dicom_value = dicom_tag
        item = item.replace(dicom_tag, dicom_value)
        text_w_values = text_w_values + item
        
    return text_w_values


def get_simulated_status(
    workflow: WorkflowDBSchema,
) -> WorkflowStatusResponseSchema:
    """
    Run a simulation of workflow progress
    and return an updated status
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
                d_directive = query_to_dict(workflow.request)['pacs_directive']
                current_status.feed_name = substitute_dicom_tags(current_status.feed_name, d_directive)
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
    update_workflow_status(args.test, wf_key)

