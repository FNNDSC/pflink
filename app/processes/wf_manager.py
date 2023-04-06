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
from utils import (
    dict_to_query,
    query_to_dict,
    dict_to_hash,
    update_workflow,
    retrieve_workflow,
)

from models import (
    State,
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
    WorkflowSchema,
)

format = "%(asctime)s: %(message)s"
logging.basicConfig(
    format=format, 
    level=logging.INFO,
    datefmt="%H:%M:%S"
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


    
def manage_workflow(dicom:dict, pfdcm_url:str,key:str) -> dict:
    """
    Manage workflow:
    Schedule task based on status 
    from the DB
    """
    workflow      = retrieve_workflow(key)
     
    if workflow.Started or not workflow.status.Status:
        # Do nothing and return
        return
                 
    cubeResource = dicom.thenArgs.CUBE
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cubeResource}/' 
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text) 

    cube_url = d_results['cubeInfo']['url']
    if dicom.PFDCMservice == "PFDCMLOCAL":
        cube_url = "http://localhost:8000/api/v1/"
      
    MAX_RETRIES   = 50
    
    pl_inst_id    = 0

      
    if not pfdcm_url:
        # Application running in test mode
        return
   
    while not workflow.status.WorkflowState == State.FEED_CREATED.name and MAX_RETRIES > 0:
        workflow.Started = True
        updated = update_workflow(key,workflow) 
        MAX_RETRIES -= 1
    
        match workflow.status.WorkflowState:
        
            case State.INITIALIZING.name:
                if workflow.Stale:
                    do_pfdcm_retrieve(dicom,pfdcm_url)                
                
            case State.RETRIEVING.name:
                if workflow.status.StateProgress == "100%" and workflow.Stale:
                    do_pfdcm_push(dicom,pfdcm_url)
                
            case State.PUSHING.name:
                if workflow.status.StateProgress == "100%" and workflow.Stale:
                    do_pfdcm_register(dicom,pfdcm_url)
                    
            case State.REGISTERING.name:
                if workflow.status.StateProgress == "100%" and workflow.Stale:
                    try:
                        pl_inst_id = do_cube_create_feed(
                        dicom.User, 
                        dicom.FeedName,
                        dicom.PACSdirective,
                        cube_url,
                        )
                    except Exception as ex:
                        logging.info("Error creating new feed: ")  
                        workflow.status.Error = "Error creating new feed: " +str(ex)
                        workflow.Started = False
                        update_workflow(key,workflow)
        
            case State.ANALYZING.name:
                return
            case State.COMPLETED.name:
                return        
        update_status(data,pfdcm_url) 
        time.sleep(10)
        
        workflow = retrieve_workflow(key)
        logging.info(workflow)
        if workflow.status.Error:
            return
            
    if pl_inst_id == 0:
        return 
    
    try:           
        do_cube_start_analysis(
                    dicom.User,
                    pl_inst_id,
                    dicom.analysisArgs,
                    cube_url,
                )
    except Exception as ex:
        logging.info("Error creating new analysis: ")
        workflow.status.Error = "Error creating new analysis: " + str(ex)
        workflow.Started = False
        update_workflow(key,workflow)


def update_status(data,pfdcm_url):
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
                   ], stdout=subprocess.PIPE,
                   stderr=subprocess.PIPE,
                   close_fds   = True
               )     
 
    
def pfdcm_do(
    verb     : str,
    thenArgs : dict,
    dicom    : dict, 
    url      : str
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
            "value"                           : dicom.PACSservice
         },
         "listenerService": {
             "value"                          : "default"
         },
         "PACSdirective": {
             "AccessionNumber"                : dicom.PACSdirective.AccessionNumber,
             "PatientID"                      : dicom.PACSdirective.PatientID,
             "PatientName"                    : dicom.PACSdirective.PatientName,
             "PatientBirthDate"               : dicom.PACSdirective.PatientBirthDate,
             "PatientAge"                     : dicom.PACSdirective.PatientAge,
             "PatientSex"                     : dicom.PACSdirective.PatientSex,
             "StudyDate"                      : dicom.PACSdirective.StudyDate,
             "StudyDescription"               : dicom.PACSdirective.StudyDescription,
             "StudyInstanceUID"               : dicom.PACSdirective.StudyInstanceUID,
             "Modality"                       : dicom.PACSdirective.Modality,
             "ModalitiesInStudy"              : dicom.PACSdirective.ModalitiesInStudy,
             "PerformedStationAETitle"        : dicom.PACSdirective.PerformedStationAETitle,
             "NumberOfSeriesRelatedInstances" : dicom.PACSdirective.NumberOfSeriesRelatedInstances,
             "InstanceNumber"                 : dicom.PACSdirective.InstanceNumber,
             "SeriesDate"                     : dicom.PACSdirective.SeriesDate,
             "SeriesDescription"              : dicom.PACSdirective.SeriesDescription,
             "SeriesInstanceUID"              : dicom.PACSdirective.SeriesInstanceUID,
             "ProtocolName"                   : dicom.PACSdirective.ProtocolName,
             "AcquisitionProtocolDescription" : dicom.PACSdirective.AcquisitionProtocolDescription,
             "AcquisitionProtocolName"        : dicom.PACSdirective.AcquisitionProtocolName,
             "withFeedBack"                   : True,
             "then"                           : verb,
             "thenArgs"                       : thenArgs,
             "dblogbasepath"                  : '/home/dicom/log',
             "json_response"                  : False
         }
    }
    st = time.time()
    response = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    et = time.time()
    elapsed_time = et - st
    logging.info(f'{bcolors.WARNING}Execution time to {verb}:{elapsed_time} seconds{bcolors.ENDC}')

         
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
                     'db'                : dicom.thenArgs.db,
                     'swift'             : dicom.thenArgs.swift, 
                     'swiftServicesPACS' : dicom.thenArgs.swiftServicesPACS,
                     'swiftPackEachDICOM': dicom.thenArgs.swiftPackEachDICOM}
                   
    
    pfdcm_do("push",thenArgs,dicom,pfdcm_url)
    
def do_pfdcm_register(dicom:dict, pfdcm_url:str):
    """
    Register PACS files to a `CUBE`
    """
    thenArgs = {
                     "db"                      : dicom.thenArgs.db,
                     "CUBE"                    : dicom.thenArgs.CUBE,
                     "swiftServicesPACS"       : dicom.thenArgs.swiftServicesPACS,
                     "parseAllFilesWithSubStr" : dicom.thenArgs.parseAllFilesWithSubStr
                   }
    pfdcm_do("register",thenArgs,dicom,pfdcm_url)


def do_cube_create_feed(userName,feedName,pacsDirective,cube_url):
    """
    Create a new feed in `CUBE` if not already present
    """
    client             =  do_cube_create_user(cube_url,userName)
    pacs_details       =  client.getPACSdetails(pacsDirective)
    feed_name          =  create_feed_name(feedName,pacs_details)
    data_path          =  client.getSwiftPath(pacsDirective)
    
    # check if feed already present
    resp = client.getFeed({"name_exact" : feedName})
    if resp['total']>0:
        return resp['data'][0]['id']
    else:    
        ## Get plugin Id 
        pluginSearchParams = {"name": "pl-dircopy"}   
        plugin_id          = client.getPluginId(pluginSearchParams)
    
        ## create a feed
        feed_params   = {'title' : feed_name,'dir' : data_path}
        feed_response = client.createFeed(plugin_id,feed_params)
        return feed_response['id']        

    
def do_cube_start_analysis(userName,previousId,analysisArgs,cube_url):
    """
    Create a new node (plugin instance) on an existing feed in `CUBE`
    """
    client                       =  do_cube_create_user(cube_url,userName)
    plugin_search_params         =  {
                                        "name"    : analysisArgs.PluginName, 
                                        "version" : analysisArgs.Version
                                    } 
    plugin_id                    =  client.getPluginId(plugin_search_params) 
    
    # split the param text
    params_text  = analysisArgs.Params.strip()
    params_dict  = params_text.split('--')
    feed_params                  =  {} 
    ##raise Exception(params_dict)
    for param in params_dict:
        if param == "":
            continue
        param = param.strip()      
        args = param.split(' ')
        feed_params[args[0]] = args[1]
        
       
    feed_params["previous_id"]   =  previousId
    
    if analysisArgs.PassUserCreds:
        feed_params["CUBEuser"]      =  userName
        feed_params["CUBEpassword"]  =  userName + "1234"
        feed_params["CUBEurl"]       =  cube_url
        
    feedResponse = client.createFeed(plugin_id,feed_params)

    
def do_cube_create_user(cubeUrl,userName):
    """
    Create a new user in `CUBE` if not already present
    """
    createUserUrl         = cubeUrl+"users/"
    userPass              = userName + "1234"
    userEmail             = userName + "@email.com"
    
    # create a new user
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
             "username" : userName,
             "password" : userPass,
             "email"    : userEmail,
             }
    resp       = requests.post(createUserUrl,json=myobj,headers=headers)
    authClient = PythonChrisClient(cubeUrl,userName,userPass)
    return authClient


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

    
if __name__== "__main__":
    """
    Main entry point to this script
    """
    d_data  =   json.loads(args.data)
    data    =   dict_to_query(d_data)
    key     =   dict_to_hash(d_data)
    manage_workflow(data,args.url,key)

    
