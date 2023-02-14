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
    
def threaded_workflow_do_while(dicom:dict, pfdcm_url:str) -> dict:
    """
    Given a dictionary object containing key-value pairs for PFDCM query & CUBE
    query, return a dictionary object as response after completing a series of
    tasks. The sequence of tasks is as follows:
        1) Use the `status` API to get the present status of the workflow
        2) If study not found, return immediately
        3) If Study is found, enter inside the while loop
            a) If study not retrieved, retrieve study using `pfdcm`
            b) If study not pushed, push study using `pfdcm`
            c) If study not registrered, register study using `pfdcm`
            d) If feed not created, create a new feed in `cube`
              i)  if `pipeline` name is specified, add a new pipeline
              ii) else add a new node
              
        4) End while loop if MAX_RETRIES == 0 or a workflow is already added in
           the feed
    """
    MAX_RETRIES = 100
    cubeResource = dicom.thenArgs.CUBE
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cubeResource}/' 
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text) 
    
    
    ## Create a Chris Client
    #client = do_cube_create_user("http://havana.tch.harvard.edu:8000/api/v1/",dicom.feedArgs.User)
    client = do_cube_create_user("http://localhost:8000/api/v1/",dicom.feedArgs.User)
    
    response = workflow_status(pfdcm_url, dicom)
    if not response.StudyFound:
        return response
    pfdcmResponse = get_pfdcm_status(pfdcm_url,dicom)
    feedName = dicom.feedArgs.FeedName
    d_dicom = pfdcmResponse['pypx']['data']
    feedName = parseFeedTemplate(feedName, d_dicom[0])

    while not response.WorkflowStarted and MAX_RETRIES>0:
        if response.StudyRetrieved:
            if response.StudyPushed:
                if response.StudyRegistered:
                    if response.FeedCreated:
                        
                        # Get previous inst Id
                        pluginInstSearchParams = {'plugin_name' : 'pl-dircopy', 'feed_id' : response.FeedId}
                        pvInstId = client.getPluginInstances(pluginInstSearchParams)['data'][0]['id']
                        workflowName = response.FeedName
                            
                        # Check if user runs a new pipeline or node
                        if dicom.feedArgs.Pipeline:
                            print(f"adding pipeline {feedName}")
                            do_cube_create_workflow(client,dicom.feedArgs.Pipeline,pvInstId,workflowName)
                        else:
                            print(f"adding new node {feedName}")
                            do_cube_create_node(client,dicom.feedArgs,pvInstId)
                    else:        
                        # wait and create a feed
                        print(f"Creating a feed {feedName}")
                        
                        ## Get the Swift path
                        dataPath = client.getSwiftPath(dicom.PACSdirective)
                        if feedName=="":
                           raise Exception("Please enter a valid feed name.") 
                        feed_id = do_cube_create_feed(client,feedName,dataPath)
                else:
                    if response.Registered == "0%":     
                        # wait and register study
                        print(f"registering study {feedName} {response.Registered}")
                        do_pfdcm_register(dicom,pfdcm_url)
                    
            else:
                if response.Pushed == "0%":  
                    print(f"pushing study {feedName} {response.Pushed}")   
                    # wait and push study
                    do_pfdcm_push(dicom,pfdcm_url)

        else:
            if response.Retrieved == "0%": 
                print(f"retrieveing study {feedName} {response.Retrieved}")   
                # wait and retrieve study
                do_pfdcm_retrieve(dicom,pfdcm_url)          
        
        MAX_RETRIES -= 1        
        # wait here for n seconds b4 polling again
        print(f"sleeping for 2 seconds")
        time.sleep(2)
        st = time.time()
        response = workflow_status(pfdcm_url, dicom)
        et = time.time()
        elapsed_time = et - st
        print(f'{bcolors.OKGREEN}Execution time to get status:{elapsed_time} seconds{bcolors.ENDC}')
           
    #end of while loop
    return response

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
    pfdcm_dicom_api = f'{url}/api/v1/PACS/thread/pypx/'
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
    d_data = json.loads(args.data)
    data = dict_to_query(d_data)
    threaded_workflow_do_while(args.url,data)

    
