from pymongo import MongoClient
import json
import hashlib
import logging
import asyncio
import time
import getopt
import argparse
from enum import Enum
from pydantic import BaseModel, Field
import requests
from client.PythonChrisClient import PythonChrisClient
format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=format, 
    level=logging.INFO,
    datefmt="%H:%M:%S"
)
    
MONGO_DETAILS = "mongodb://localhost:27017"

client = MongoClient(MONGO_DETAILS)

database = client.workflows

workflow_collection = database.get_collection("workflows_collection")

from models import (
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
    WorkflowSchema,
)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--url', metavar='N', type=str)
parser.add_argument('--key', metavar='N', type=str)
args = parser.parse_args()



# helpers


def workflow_retrieve_helper(workflow:dict) -> WorkflowSchema:    
    request =  DicomStatusQuerySchema(
                   PFDCMservice  = workflow["request"]["PFDCMservice"],
                   PACSservice   = workflow["request"]["PACSservice"],
                   PACSdirective = workflow["request"]["PACSdirective"],
                   dblogbasepath = workflow["request"]["dblogbasepath"],
                   FeedName      = workflow["request"]["FeedName"],
                   User          = workflow["request"]["User"],
               )
    return WorkflowSchema(
        key      = workflow["_id"],
        request  = request,
        status   = workflow["status"],
    )
    
def workflow_add_helper(workflow:WorkflowSchema) -> dict:
    d_request = {
        "PFDCMservice"   : workflow.request.PFDCMservice,
        "PACSservice"    : workflow.request.PACSservice,
        "PACSdirective"  : workflow.request.PACSdirective.__dict__,
        "dblogbasepath"  : workflow.request.dblogbasepath,
        "FeedName"       : workflow.request.FeedName,
        "User"           : workflow.request.User,
    }
    
    return {
        "_id"     : workflow.key,
        "request" : d_request,
        "status"  : workflow.status.__dict__,
    }

def dict_to_query(query:dict)->DicomStatusQuerySchema:
    return DicomStatusQuerySchema(
                   PFDCMservice  = query["PFDCMservice"],
                   PACSservice   = query["PACSservice"],
                   PACSdirective = query["PACSdirective"],
                   dblogbasepath = query["dblogbasepath"],
                   FeedName      = query["FeedName"],
                   User          = query["User"],
               )
               
def update_workflow(key:str, data:dict):
    """
    Update an existing workflow in the DB
    """
    workflow = workflow_collection.find_one({"_id":key})
    if workflow:
        updated_workflow = workflow_collection.update_one(
            {"_id":key},{"$set":workflow_add_helper(data)}
        )
        if updated_workflow:
            return True
        return False    
    
def retrieve_workflow(key:str) -> dict:
    """
    Retrieve a single workflow from DB
    Given: key
    """
    workflow = workflow_collection.find_one({"_id":key})
    if workflow:
        return workflow_retrieve_helper(workflow)
    
def update_workflow_status(key:str,status:DicomStatusResponseSchema):
    workflow = retrieve_workflow(key)
    if workflow.status.Stale: 
        logging.info(f"WORKING on updating the status for {key}, locking--")       
        workflow.status.Stale=False
        update_workflow(key,workflow)
        workflow.status = status
        workflow.status.Stale=True    
        update_workflow(key,workflow)
        logging.info(f"UPDATED status for {key}, releasing lock")


    
def workflow_status(
    pfdcm_url : str,
    key       : str,
    dicom     : dict,
) -> dict:
    """
    Return the status of a workflow in `pflink`
    by asking `pfdcm` & `cube`. The sequence is as
    follows:
        1) Ask `pfdcm` about the status of a study
        2) Ask `cube` about the status of the feed created using the study
        3) Parse both the results to a response schema
        4) Return the response
    """
    # Ask `pfdcm` for study
    pfdcm_resp = get_pfdcm_status(pfdcm_url,dicom)
    
    # Ask `CUBE` for feed
    cube_resp = get_feed_status(pfdcm_resp,dicom)
    
    # Parse both the respones
    status = parse_response(pfdcm_resp, cube_resp)
    
    # return the response
    update_workflow_status(key,status)
      
def get_pfdcm_status(pfdcm_url,dicom):
    """
    Get the status of PACS from `pfdcm`
    by running the syncronous API of `pfdcm`
    """
    pfdcm_dicom_api = f'{pfdcm_url}/api/v1/PACS/sync/pypx/'
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
        "PACSservice": {
          "value": dicom.PACSservice
        },
        "listenerService": {
          "value": "default"
         },
        "PACSdirective": {
          "AccessionNumber": dicom.PACSdirective.AccessionNumber,
          "PatientID": dicom.PACSdirective.PatientID,
          "PatientName": dicom.PACSdirective.PatientName,
          "PatientBirthDate": dicom.PACSdirective.PatientBirthDate,
          "PatientAge": dicom.PACSdirective.PatientAge,
          "PatientSex": dicom.PACSdirective.PatientSex,
          "StudyDate": dicom.PACSdirective.StudyDate,
          "StudyDescription": dicom.PACSdirective.StudyDescription,
          "StudyInstanceUID": dicom.PACSdirective.StudyInstanceUID,
          "Modality": dicom.PACSdirective.Modality,
          "ModalitiesInStudy": dicom.PACSdirective.ModalitiesInStudy,
          "PerformedStationAETitle": dicom.PACSdirective.PerformedStationAETitle,
          "NumberOfSeriesRelatedInstances": dicom.PACSdirective.NumberOfSeriesRelatedInstances,
          "InstanceNumber": dicom.PACSdirective.InstanceNumber,
          "SeriesDate": dicom.PACSdirective.SeriesDate,
          "SeriesDescription": dicom.PACSdirective.SeriesDescription,
          "SeriesInstanceUID": dicom.PACSdirective.SeriesInstanceUID,
          "ProtocolName": dicom.PACSdirective.ProtocolName,
          "AcquisitionProtocolDescription": dicom.PACSdirective.AcquisitionProtocolDescription,
          "AcquisitionProtocolName": dicom.PACSdirective.AcquisitionProtocolName,
          "withFeedBack": True,
          "then": 'status',
          "thenArgs": "",
          "dblogbasepath": dicom.dblogbasepath,
          "json_response": True
        }
      }

    response = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    return json.loads(response.text) 

def get_feed_status(pfdcmResponse: dict, dicom: dict):
    """
    Get the status of a feed inside `CUBE`
    """
        
    cubeResponse = {
        "FeedName" : "",
        "FeedCreated" : False,
        "FeedProgress" : "Not started",
        "WorkflowStarted": False,
        "FeedStatus" : "",
        "FeedError" : "",
        "FeedId" : ""}
        
    feedName = dicom.FeedName
    d_dicom = pfdcmResponse['pypx']['data']
    if d_dicom:
        feedName = parseFeedTemplate(feedName, d_dicom[0])        
    if feedName == "":
        cubeResponse['FeedError'] = "Please enter a valid feed name"
        
    #cl = do_cube_create_user("http://havana.tch.harvard.edu:8000/api/v1/",dicom.feedArgs.User) 
    cl = do_cube_create_user("http://localhost:8000/api/v1/",dicom.User)  
    resp = cl.getFeed({"name_exact" : feedName})
    if resp['total']>0:
        cubeResponse['FeedCreated'] = True
        cubeResponse['FeedName'] = resp['data'][0]['name']
        cubeResponse['FeedId'] = resp['data'][0]['id']
        
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

        if total>1:
            cubeResponse['WorkflowStarted'] = True
            feedProgress = round((finished/total) * 100)
            cubeResponse['FeedProgress'] = str(feedProgress) + "%"
            feedStatus = ""
            if errored>0 or cancelled>0:
                cubeResponse['FeedError'] = str(errored + cancelled) + " job(s) failed"
                feedStatus = "Failed"
            else:
                if feedProgress==100:
                    feedStatus = "Complete"
                else:
                    feedStatus = "In progress"
             
            cubeResponse['FeedStatus'] = feedStatus
            
            
    return cubeResponse
def parse_response(
    pfdcmResponse : dict, 
    cubeResponse : dict 
) -> dict:
    """
    Parse JSON object for workflow status response
    """
    status = DicomStatusResponseSchema()
    data = pfdcmResponse['pypx']['data']
    study = pfdcmResponse['pypx']['then']['00-status']['study']
    if study:
        status.StudyFound = True
        images = study[0][data[0]['StudyInstanceUID']['value']][0]['images'] 
  
        totalImages = images["requested"]["count"]
        totalRetrieved = images["packed"]["count"]
        totalPushed = images["pushed"]["count"]
        totalRegistered = images["registered"]["count"]
        
        if totalImages>0:       
            totalRetrievedPerc = round((totalRetrieved/totalImages)*100)
            totalPushedPerc = round((totalPushed/totalImages)*100)
            totalRegisteredPerc = round((totalRegistered/totalImages)*100)
        
            status.Retrieved  = str (totalRetrievedPerc) + "%"
            status.Pushed = str(totalPushedPerc) + "%"
            status.Registered = str(totalRegisteredPerc) + "%"
        
        
            if totalRetrievedPerc == 100:
                status.StudyRetrieved = True
            if totalPushedPerc == 100:
                status.StudyPushed = True
            if totalRegisteredPerc == 100:
                status.StudyRegistered = True
    else:
        status.Error = "Study not found. Please enter valid study info"
        
    if cubeResponse:
        status.WorkflowState = cubeResponse['FeedCreated']
        status.FeedId = cubeResponse['FeedId']
        status.FeedName = cubeResponse['FeedName']
        status.FeedProgress = cubeResponse['FeedProgress']
        status.FeedStatus = cubeResponse['FeedStatus']
        status.Error = cubeResponse['FeedError']
        
        
    return status 

def do_cube_create_user(cubeUrl,userName):
    """
    Create a new user in `CUBE` if not already present
    """
    createUserUrl = cubeUrl+"users/"
    userPass = userName + "1234"
    userEmail = userName + "@email.com"
    
    # create a new user
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
             "username" : userName,
             "password" : userPass,
             "email"    : userEmail,
             }
    resp = requests.post(createUserUrl,json=myobj,headers=headers)

    authClient = PythonChrisClient(cubeUrl,userName,userPass)
    return authClient
    
def parseFeedTemplate(
    feedTemplate : str, 
    dcmData : dict
) -> str:
    """
    # Given a feed name template, substitute dicom values
    # for specified dicom tags
    """
    items = feedTemplate.split('%')
    feedName = ""
    for item in items:
        if item == "":
            continue;
        tags = item.split('-')
        dicomTag = tags[0]
        try:        
            dicomValue = dcmData[dicomTag]["value"]
        except:
            dicomValue = dicomTag
        item = item.replace(dicomTag,dicomValue)
        feedName = feedName + item
    return feedName    
    
if __name__== "__main__":
    d_data = json.loads(args.data)
    data = dict_to_query(d_data)
    resp = workflow_status(args.url,args.key,data) 
