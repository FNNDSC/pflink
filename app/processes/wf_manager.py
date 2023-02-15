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
import  subprocess
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
    State,
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
    WorkflowSchema,
)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--data', metavar='N', type=str)
parser.add_argument('--url', metavar='N', type=str)

args = parser.parse_args()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# helpers


def workflow_retrieve_helper(workflow:dict) -> WorkflowSchema:    
    request =  DicomStatusQuerySchema(
                   PFDCMservice  = workflow["request"]["PFDCMservice"],
                   PACSservice   = workflow["request"]["PACSservice"],
                   PACSdirective = workflow["request"]["PACSdirective"],
                   thenArgs      = workflow["request"]["thenArgs"],
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
        "thenArgs"       : workflow.request.thenArgs.__dict__,
        "dblogbasepath"  : workflow.request.dblogbasepath,
        "FeedName"       : workflow.request.FeedName,
        "User"           : workflow.request.User,
    }
    
    return {
        "_id"     : workflow.key,
        "request" : d_request,
        "status"  : workflow.status.__dict__,
    }
    
def dict_to_query(request:dict)-> DicomStatusQuerySchema:
    return DicomStatusQuerySchema(
        PFDCMservice   = request["PFDCMservice"],
        PACSservice    = request["PACSservice"],
        PACSdirective  = request["PACSdirective"],
        thenArgs       = request["thenArgs"],
        dblogbasepath  = request["dblogbasepath"],
        FeedName       = request["FeedName"],
        User           = request["User"],
    )

def query_to_dict(request:DicomStatusQuerySchema)-> dict:
    return {
        "PFDCMservice"   : request.PFDCMservice,
        "PACSservice"    : request.PACSservice,
        "PACSdirective"  : request.PACSdirective.__dict__,
        "thenArgs"       : request.thenArgs.__dict__,
        "dblogbasepath"  : request.dblogbasepath,
        "FeedName"       : request.FeedName,
        "User"           : request.User,
    }
    
def dict_to_hash(data:dict) -> str:
    # convert to string and encode
    str_data = json.dumps(data)
    hash_request = hashlib.md5(str_data.encode())     
    # create an unique key
    key = hash_request.hexdigest()
    return key

# DB queries

                   
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
    
def manage_workflow(dicom:dict, pfdcm_url:str,key:str) -> dict:
    """
    Manage workflow:
    Schedule task based on status 
    from the DB
    """
    workflow = retrieve_workflow(key)
    if workflow.status.Started:
        # Do nothing adnd return
        return
        
    workflow.status.Started = True
    update_workflow(key,workflow)
    
    while not workflow.status.WorkflowState == State.REGISTERED.name:
        
        if workflow.status.WorkflowState == State.NOT_STARTED.name:
            if workflow.status.Retrieved == "0%":
                do_pfdcm_retrieve(dicom,pfdcm_url)
        elif workflow.status.WorkflowState == State.RETRIEVED.name:
            if workflow.status.Pushed == "0%":
                do_pfdcm_push(dicom,pfdcm_url)
        elif workflow.status.WorkflowState == State.PUSHED.name:
            if workflow.status.Registered == "0%":
                do_pfdcm_register(dicom,pfdcm_url)        
        
        update_status(data,pfdcm_url,key)
        time.sleep(4)
        workflow = retrieve_workflow(key)
        if workflow.status.Error:
            return

def update_status(data,pfdcm_url,key):
    """
    Trigger an update status in 
    a separate python process
    """
    d_data   = query_to_dict(data)
    str_data = json.dumps(d_data)
    process  = subprocess.Popen(
                   ['python',
                   'app/processes/status.py',
                   "--data",str_data,
                   "--url",pfdcm_url,
                   "--key",key
                   ], stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   close_fds   = True
               )       
 
    
def pfdcm_do(
    verb : str,
    thenArgs:dict,
    dicom : dict, 
    url : str
) -> dict:
    """
    A reusable method to either retrieve, push or register dicoms using pfdcm
    by running the threaded API of `pfdcm`
    """
    thenArgs = json.dumps(thenArgs,separators=(',', ':'))    
    pfdcm_dicom_api = f'{url}/api/v1/PACS/sync/pypx/'
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
             "then": verb,
             "thenArgs": thenArgs,
             "dblogbasepath": '/home/dicom/log',
             "json_response": False
         }
    }
    st = time.time()
    response = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    et = time.time()
    elapsed_time = et - st
    print(f'{bcolors.WARNING}Execution time to {verb}:{elapsed_time} seconds{bcolors.ENDC}')
         
def do_pfdcm_retrieve(dicom:dict, pfdcm_url:str):
    """
    Retrieve PACS using pfdcm
    """
    thenArgs = ""   
    pfdcm_do("retrieve",thenArgs,dicom,pfdcm_url)
    
def do_pfdcm_push(dicom:dict, pfdcm_url:str):
    """
    Push PACS to a Swift store using `pfdcm`
    """

    thenArgs = {
                     'db': dicom.thenArgs.db,
                     'swift': dicom.thenArgs.swift, 
                     'swiftServicesPACS': dicom.thenArgs.swiftServicesPACS,
                     'swiftPackEachDICOM': dicom.thenArgs.swiftPackEachDICOM}
                   
    
    pfdcm_do("push",thenArgs,dicom,pfdcm_url)
    
def do_pfdcm_register(dicom:dict, pfdcm_url:str):
    """
    Register PACS files to a `CUBE`
    """
    thenArgs = {
                     "db": dicom.thenArgs.db,
                     "CUBE": dicom.thenArgs.CUBE,
                     "swiftServicesPACS": dicom.thenArgs.swiftServicesPACS,
                     "parseAllFilesWithSubStr": dicom.thenArgs.parseAllFilesWithSubStr
                   }
    pfdcm_do("register",thenArgs,dicom,pfdcm_url)

def do_cube_create_feed(client,feedName,dataPath):
    """
    Create a new feed in `CUBE` if not already present
    """
    # check if feed already present
    resp = client.getFeed({"name_exact" : feedName})
    if resp['total']>0:
        return resp['data'][0]['id']
    else:    
        ## Get plugin Id 
        pluginSearchParams = {"name": "pl-dircopy"}   
        plugin_id = client.getPluginId(pluginSearchParams)
    
        ## create a feed
        feedParams = {'title' : feedName,'dir' : dataPath}
        feedResponse = client.createFeed(plugin_id,feedParams)
        return feedResponse['id']
    
def do_cube_create_workflow(client,pipelineName,feedId,workflowName):
    """
    Create a new workflow on an existing feed in `CUBE` if not already present
    """
    resp = client.getWorkflow({'title':workflowName})
    if resp['total']>0:
        return resp
    else:
        ## Get pipeline id
        pipelineSearchParams = {'name':pipelineName}
        pipeline_id = client.getPipelineId(pipelineSearchParams)
        
        if pipeline_id<0:
            raise Exception(f'Pipeline {pipelineName} does not exist')
        ## Create a workflow
        wfParams = {'previous_plugin_inst_id':feedId, 'title' : workflowName}
        wfResponse = client.createWorkflow(pipeline_id, wfParams)
        return wfResponse
            
    
def do_cube_create_node(client,feedArgs,feedId):
    """
    Create a new node (plugin instance) on an existing feed in `CUBE`
    """
    pluginSearchParams = {"name": feedArgs.nodeArgs.PluginName, "version": feedArgs.nodeArgs.Version}   
    plugin_id = client.getPluginId(pluginSearchParams)
    feedParams = feedArgs.nodeArgs.Params
    feedParams["previous_id"] = feedId
    if feedArgs.nodeArgs.PassUserCreds:
        feedParams["username"] = feedArgs.User
        feedParams["password"] = feedArgs.User + "1234"
    feedResponse = client.createFeed(plugin_id,feedParams)
    
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
    d_data  =   json.loads(args.data)
    data    =   dict_to_query(d_data)
    key     =   dict_to_hash(d_data)
    manage_workflow(data,args.url,key)

    
