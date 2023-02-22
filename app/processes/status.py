import json
import logging
import argparse
import requests
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
    if not workflow.status.Stale or  workflow.status.WorkflowState ==  State.COMPLETED.name:             
        # Do nothing and exit
        return 
    logging.info(f"WORKING on updating the status for {key}, locking--")       
    workflow.status.Stale=False
    update_workflow(key,workflow)
    
    updated_status         = _get_workflow_status(pfdcm_url,key,query)
    workflow.status        = updated_status
    workflow.status.Stale  = True  
      
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
    pfdcm_resp    = _get_pfdcm_status(pfdcm_url,dicom)
    cube_resp     = _get_feed_status(pfdcm_resp,dicom)
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


def _get_feed_status(pfdcmResponse: dict, dicom: dict):
    """
    Get the status of a feed inside `CUBE`
    """
    MAX_JOBS = 2
        
    cubeResponse = {
        "FeedName"       : "",
        "FeedState"      : "",
        "FeedProgress"   : "Not started",
        "FeedStatus"     : "",
        "FeedError"      : "",
        "FeedId"         : ""
    }
        
    feedName = dicom.FeedName
    d_dicom = pfdcmResponse['pypx']['data']
    if d_dicom:
        feedName = _parse_feed_template(feedName, d_dicom[0])        
    if feedName == "":
        cubeResponse['FeedError'] = "Please enter a valid feed name"
        
    try:     
        cl = _do_cube_create_user("http://localhost:8000/api/v1/",dicom.User) 
    except:
        raise Exception (f"Could not find or create user with username {dicom.User}")
        
    resp = cl.getFeed({"name_exact" : feedName})
    if resp['total']>0:
        cubeResponse['FeedState']       = State.FEED_CREATED.name
        cubeResponse['FeedName']        = resp['data'][0]['name']
        cubeResponse['FeedId']          = resp['data'][0]['id']
        
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
            cubeResponse['FeedState']     = State.ANALYSIS_STARTED.name
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
    data     = pfdcmResponse['pypx']['data']
    study    = pfdcmResponse['pypx']['then']['00-status']['study']
    
    if study:
        status.StudyFound  = True
        images             = study[0][data[0]['StudyInstanceUID']['value']][0]['images'] 
        totalImages        = images["requested"]["count"]
        totalRetrieved     = images["packed"]["count"]
        totalPushed        = images["pushed"]["count"]
        totalRegistered    = images["registered"]["count"]
        
        if totalImages>0:       
            totalRetrievedPerc  = round((totalRetrieved/totalImages)*100)
            totalPushedPerc     = round((totalPushed/totalImages)*100)
            totalRegisteredPerc = round((totalRegistered/totalImages)*100)        
            status.Retrieved    = str (totalRetrievedPerc) + "%"
            status.Pushed       = str(totalPushedPerc) + "%"
            status.Registered   = str(totalRegisteredPerc) + "%"       
        
            if totalRetrievedPerc == 100:
                status.WorkflowState = State.RETRIEVED.name
            if totalPushedPerc == 100:
                status.WorkflowState = State.PUSHED.name
            if totalRegisteredPerc == 100:
                status.WorkflowState = State.REGISTERED.name
    else:
        status.Error = "Study not found. Please enter valid study info"
        
    if cubeResponse:           
       if cubeResponse['FeedState'] != "":
            status.WorkflowState   = cubeResponse['FeedState']           
            status.FeedId          = cubeResponse['FeedId']
            status.FeedName        = cubeResponse['FeedName']
            status.FeedProgress    = cubeResponse['FeedProgress']
            status.FeedStatus      = cubeResponse['FeedStatus']       
            status.FeedStatus      = cubeResponse['FeedStatus']
            
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
    # Given a feed name template, substitute dicom values
    # for specified dicom tags
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
 
    
if __name__== "__main__":
    """
    Main entry point
    """
    d_data  =   json.loads(args.data)
    data    =   dict_to_query(d_data)
    key     =   dict_to_hash(d_data)
    resp = workflow_status(args.url,key,data) 
