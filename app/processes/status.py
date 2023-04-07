import json
import logging
import argparse
import requests
import random
from client.PythonChrisClient import PythonChrisClient
from models import (
    State,
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
    WorkflowSchema,
)
from utils import (
    dict_to_query,
    query_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
)


format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=format, 
    level=logging.INFO,
    datefmt="%H:%M:%S"
)
    

parser = argparse.ArgumentParser(description='Process arguments passed through CLI')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--url', metavar='N', type=str)

args = parser.parse_args()

    
def workflow_status(
    pfdcm_url : str,
    key       : str,
    query     : DicomStatusQuerySchema
):
    """
    Update the status of a workflow object
    in the DB
    """
    workflow = retrieve_workflow(key)
    if not workflow.Stale or  workflow.status.WorkflowState ==  State.COMPLETED.name:             
        # Do nothing and exit
        return
         
    logging.info(f"WORKING on updating the status for {key}, locking--")       
    workflow.Stale=False
    update_workflow(key,workflow)
    
    if not pfdcm_url:
        # Application running in test mode
        updated_status         = _test_status_progress(workflow.status,query)
    else:
        updated_status         = _get_workflow_status(pfdcm_url,key,query)
    
    workflow.status        = updated_status
    workflow.Stale         = True  
      
    update_workflow(key,workflow)
    logging.info(f"UPDATED status for {key}, releasing lock")


    
def _get_workflow_status(
    pfdcm_url : str,
    key       : str,
    dicom     : DicomStatusQuerySchema,
) -> DicomStatusResponseSchema:
    """
    Return the status of a workflow in `pflink`
    by asking `pfdcm` & `cube`. The sequence is as
    follows:
        1) Ask `pfdcm` about the status of a study
        2) Ask `cube` about the status of the feed created using the study
        3) Parse both the results to a response schema
        4) Return the response
    """
    
    cubeResource = dicom.thenArgs.CUBE
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cubeResource}/' 
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text) 
    cube_url = d_results['cubeInfo']['url']

    pfdcm_resp    = _get_pfdcm_status(pfdcm_url,dicom)
    cube_resp     = _get_feed_status(pfdcm_resp,dicom,cube_url)
    status        = _parse_response(pfdcm_resp, cube_resp,key)
    return status
      
def _get_pfdcm_status(pfdcm_url,dicom):
    """
    Get the status of PACS from `pfdcm`
    by running the syncronous API of `pfdcm`
    """
    pfdcm_status_url = f'{pfdcm_url}/api/v1/PACS/sync/pypx/'
    headers          = {'Content-Type': 'application/json','accept': 'application/json'}
    
    myobj = {
        "PACSservice": {
          "value"                         : dicom.PACSservice
        },
        "listenerService": {
          "value"                         : "default"
         },
        "PACSdirective": {
          "AccessionNumber"               : dicom.PACSdirective.AccessionNumber,
          "PatientID"                     : dicom.PACSdirective.PatientID,
          "PatientName"                   : dicom.PACSdirective.PatientName,
          "PatientBirthDate"              : dicom.PACSdirective.PatientBirthDate,
          "PatientAge"                    : dicom.PACSdirective.PatientAge,
          "PatientSex"                    : dicom.PACSdirective.PatientSex,
          "StudyDate"                     : dicom.PACSdirective.StudyDate,
          "StudyDescription"              : dicom.PACSdirective.StudyDescription,
          "StudyInstanceUID"              : dicom.PACSdirective.StudyInstanceUID,
          "Modality"                      : dicom.PACSdirective.Modality,
          "ModalitiesInStudy"             : dicom.PACSdirective.ModalitiesInStudy,
          "PerformedStationAETitle"       : dicom.PACSdirective.PerformedStationAETitle,
          "NumberOfSeriesRelatedInstances": dicom.PACSdirective.NumberOfSeriesRelatedInstances,
          "InstanceNumber"                : dicom.PACSdirective.InstanceNumber,
          "SeriesDate"                    : dicom.PACSdirective.SeriesDate,
          "SeriesDescription"             : dicom.PACSdirective.SeriesDescription,
          "SeriesInstanceUID"             : dicom.PACSdirective.SeriesInstanceUID,
          "ProtocolName"                  : dicom.PACSdirective.ProtocolName,
          "AcquisitionProtocolDescription": dicom.PACSdirective.AcquisitionProtocolDescription,
          "AcquisitionProtocolName"       : dicom.PACSdirective.AcquisitionProtocolName,
          "withFeedBack"                  : True,
          "then"                          : 'status',
          "thenArgs"                      : "",
          "dblogbasepath"                 : dicom.dblogbasepath,
          "json_response"                 : True
        }
      }

    response = requests.post(
                   pfdcm_status_url, 
                   json = myobj, 
                   headers=headers
               )

    return json.loads(response.text) 


def _get_feed_status(pfdcmResponse: dict, dicom: dict, cube_url: str):
    """
    Get the status of a feed inside `CUBE`
    """
    MAX_JOBS = 12
        
    cubeResponse = {
        "FeedName"       : "",
        "FeedState"      : "",
        "FeedProgress"   : "0%",
        "FeedStatus"     : "",
        "FeedError"      : "",
        "FeedId"         : ""
    }
        
    feedName = dicom.FeedName
    
    try:
        d_dicom  = pfdcmResponse['pypx']['data'][0]['series']
    
        if d_dicom:
            feedName = _parse_feed_template(feedName, d_dicom[0])        
        if feedName == "":
            cubeResponse['FeedError'] = "Please enter a valid feed name"
    except Exception as ex:
        cubeResponse["FeedError"] = str(ex)
      
    try:     
        cl = _do_cube_create_user(cube_url,dicom.User) 
    except Exception as ex:
        cubeResponse['FeedError'] = str(ex)

    resp = {}
    try:    
        resp = cl.getFeed({"name_exact" : feedName})
    except Exception as ex:
        cubeResponse["FeedError"] = str(ex)

    valid = resp.get('total')
    if not valid:
        return cubeResponse

    if resp['total']>0:
        cubeResponse['FeedState']       = State.FEED_CREATED.name
        cubeResponse['FeedName']        = resp['data'][0]['name']
        cubeResponse['FeedId']          = resp['data'][0]['id']
        cubeResponse['FeedProgress']    = "100%"
        
        # total jobs in the feed
        created            = resp['data'][0]['created_jobs']
        waiting            = resp['data'][0]['waiting_jobs']
        scheduled          = resp['data'][0]['scheduled_jobs']
        started            = resp['data'][0]['started_jobs']
        registering        = resp['data'][0]['registering_jobs']
        finished           = resp['data'][0]['finished_jobs']
        errored            = resp['data'][0]['errored_jobs']
        cancelled          = resp['data'][0]['cancelled_jobs']
        
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
        status.Error  = "Study not found. Please enter valid study info"
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
    
def create_feed_name(
    feedTemplate : str, 
    dcmData : dict
) -> str:
    """
    # Given a feed name template, substitute dicom values
    # for specified dicom tags
    """
    items     = feedTemplate.split('%')
    feedName  = ""
    for item in items:
        if item == "":
            continue;
            
        tags      = item.split('-')
        dicomTag  = tags[0]
        
        try:        
            dicomValue = dcmData[dicomTag]
        except:
            dicomValue = dicomTag
            
        item       = item.replace(dicomTag,dicomValue)
        feedName   = feedName + item
        
    return feedName
    
def _test_status_progress(
    status    : dict,
    query     : DicomStatusQuerySchema,
) -> DicomStatusResponseSchema:
    """
    Run a simulation of workflow progress
    and update the database
    """
    NODES = {
              25 : "pl-lld_inference",
              50 : "pl-markimg",
              75 : "pl-img2dcm",
              100: "pl-orthanc_push",
            }
        
    TOTAL_NODES         = 8
    MAX_N               = 9999
    PROGRESS_JUMP       = 25
    status.Error        = ""
        
    match status.WorkflowState:
    
        case State.INITIALIZING.name:
            status.WorkflowState   = State(1).name
            status.StateProgress   = "25%"
         
        case State.RETRIEVING.name: 
            progress                = __get_progress_from_text(status.StateProgress)
            if progress >= 100:                
                status.WorkflowState    = State(2).name
                status.StateProgress    = '25%' 
            else:                     
                progress               += PROGRESS_JUMP
                status.StateProgress    = str(progress) + '%' 
                 
        case State.PUSHING.name:
            progress                = __get_progress_from_text(status.StateProgress)
            if progress >= 100:              
                status.WorkflowState    = State(3).name
                status.StateProgress    = '25%'
            else:
                progress                  += PROGRESS_JUMP
                status.StateProgress       = str(progress) + '%'
              
                
        case State.REGISTERING.name:
            progress                = __get_progress_from_text(status.StateProgress)
            if progress >= 100:             
                status.WorkflowState    = State(4).name
                status.StateProgress    = '100%'
                status.FeedId           = random.randint(0,MAX_N)
                d_directive             = query_to_dict(query)['PACSdirective']
                status.FeedName         = dict_to_hash(d_directive)
            else:
                progress              += PROGRESS_JUMP
                status.StateProgress   = str(progress) + '%'
              
                
        case State.FEED_CREATED.name:
            status.WorkflowState    = State(5).name
            status.StateProgress    = '25%'                            
                 
                       
        case State.ANALYZING.name:
            progress                = __get_progress_from_text(status.StateProgress)
            if progress >= 100:                
                status.WorkflowState    = State(6).name
            else:
                status.CurrentNode   = [NODES[progress]]
                progress            += PROGRESS_JUMP
                status.StateProgress = str(progress) + '%'            
               
    return status   
    
def __get_progress_from_text(progress:str):
    """
    Convert progress percentage defined in text to integer
    """
    progress = progress.replace('%','')
    return int(progress)

    
if __name__== "__main__":
    """
    Main entry point
    """
    d_data  =   json.loads(args.data)
    data    =   dict_to_query(d_data)
    key     =   dict_to_hash(d_data)
    resp = workflow_status(args.url,key,data) 
