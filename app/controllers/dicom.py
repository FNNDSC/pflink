import motor.motor_asyncio
from bson.objectid import ObjectId
import requests
import json
from controllers.PythonChrisClient import PythonChrisClient
from datetime import datetime
import time
import threading
import asyncio

from controllers.pfdcm import (
    retrieve_pfdcm,
    retrieve_pfdcms,
)
from models.dicom import (
    DicomStatusResponseSchema,
)

job_checklist = {
                  1 : "retrieve",
                  2 : "push",
                  3 : "register",
                  4 : "create feed",
                  5 : "create workflow"
                }
    
# Get the status about a dicom inside pfdcm using its series_uid & study_uid
async def dicom_status(dicom: dict) -> dict:
    
    pfdcm_name = dicom.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)
    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    pfdcm_dicom_api = f'{pfdcm_url}/api/v1/PACS/sync/pypx/'
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
        "PACSservice": {
          "value": dicom.PACSservice
        },
        "listenerService": {
          "value": dicom.listenerService
         },
        "PACSdirective": {
          "SeriesInstanceUID": dicom.SeriesInstanceUID,
          "StudyInstanceUID": dicom.StudyInstanceUID,
          "withFeedBack": True,
          "then": 'status',
          "thenArgs": "",
          "dblogbasepath": dicom.dblogbasepath,
          "json_response": True
        }
      }

    response = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    d_results = json.loads(response.text)  
    exists =  d_results['pypx']['then']['00-status']['study']
    feedTemplate = dicom.feedArgs.FeedName

    dicomResponse = DicomStatusResponseSchema()
    d_dicom = d_results['pypx']['data']
    feedName = feedTemplate
    
        
    if exists:
        dicomResponse = parseResponse(exists[0][dicom.StudyInstanceUID][0]['images'])
    else:
        dicomResponse.Message = "Study not found"
    if d_dicom:
        feedName = parseFeedTemplate(feedTemplate, d_dicom[0])        
        dicomResponse.DicomData = d_dicom[0]


    cl = PythonChrisClient("http://localhost:8000/api/v1/","chris","chris1234")
    resp = cl.getFeed({"plugin_name" : "pl-dircopy", "title" : feedName})
    if resp['total']>0:
        dicomResponse.FeedCreated = True
        dicomResponse.FeedName = resp['data'][0]['title']
        wfResp = cl.getWorkflow({"title" : feedName})
        if wfResp['total']>0:
            dicomResponse.WorkflowStarted = True
            instResp = cl.getWorkflowDetails(wfResp['data'][0]['id'])
            finishedNodes = 1
            feedStatus = "In Progress"
            feedError = ""
            for pInst in instResp['data']:
                status = pInst['status']
                if status == "finishedSuccessfully":
                    finishedNodes += 1
                if status == "cancelled" or status == "finishedWithError":
                    feedStatus = "Failed"
                    feedError += pInst['plugin_name'] + " : " + pInst['status'] + ", "
            dicomResponse.FeedProgress = str (round(finishedNodes/(len(instResp['data']) + 1)*100)) + "%"
            if finishedNodes == len(instResp['data']) + 1:
                feedStatus = "Completed"
            dicomResponse.FeedStatus = feedStatus
            dicomResponse.Error = feedError
                    
        
    return dicomResponse                      
    
 
# Retrieve/push/register a dicom using pfdcm (WIP) 
#
#
         
async def run_dicom_workflow(dicom:dict) -> dict:
    response = await dicom_status(dicom)
    while not response.WorkflowStarted:
        if response.StudyFound:
            await dicom_do("retrieve",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
        if response.Retrieved == "100%":
            await dicom_do("push",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
        if response.Pushed == "100%":
            await dicom_do("register",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
        if response.Registered == "100%":
            feedName = parseFeedTemplate(dicom.feedArgs.FeedName,response.DicomData)
            feedParams = {"dicomStudyUID" : dicom.StudyInstanceUID,
                  "pipeline_name" : dicom.feedArgs.Pipeline,
                  "plugin_name"   : "pl-dircopy",
                  "feed_name"     : feedName,
                  "pfdcm_name"    : dicom.PFDCMservice,
                  "cube_name"     : dicom.thenArgs.CUBE}
    
            response = await startFeed(feedParams)
        time.sleep(2)
        response = await dicom_status(dicom)
    
    return response

### Helper Methods ###

# Given a feed name template, substitute dicom values
# for specified dicom tags
def parseFeedTemplate(feedTemplate : str, dcmData : dict) -> str:
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
    
    
async def dicom_do(verb : str,study_id : str,series_id : str) -> dict:
    if verb=="retrieve":
        thenArgs = ""
    elif verb == "push":

         thenArgs = {'db':'/home/dicom/log',
                     'swift':"local", 
                     'swiftServicesPACS':'orthanc',
                     'swiftPackEachDICOM':True}
                   
    elif verb=="register":
        thenArgs = {
                     "db": "/home/dicom/log",
                     "CUBE": "local",
                     "swiftServicesPACS": "orthanc",
                     "parseAllFilesWithSubStr": "dcm"
                   }
    thenArgs = json.dumps(thenArgs,separators=(',', ':'))
    
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_dicom_api = f'{pfdcm_url}/api/v1/PACS/thread/pypx/'
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
  "PACSservice": {
    "value": 'orthanc'
  },
  "listenerService": {
    "value": "default"
  },
  "PACSdirective": {
    "StudyInstanceUID": study_id,
    "SeriesInstanceUID": series_id,
    "withFeedBack": True,
    "then": verb,
    "thenArgs": thenArgs,
    "dblogbasepath": '/home/dicom/log',
    "json_response": False
  }
}

    response = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    d_results = json.loads(response.text) 
    return d_results
    
## Parse JSON object for status
##
##
##
##
def parseResponse( response : dict) -> dict:
    totalImages = response["requested"]["count"]
    totalRetrieved = response["packed"]["count"]
    totalPushed = response["pushed"]["count"]
    totalRegistered = response["registered"]["count"]
    
    status = DicomStatusResponseSchema(
               Retrieved  = str (round((totalRetrieved/totalImages)*100)) + "%",
               Pushed = str(round((totalPushed/totalImages)*100)) + "%",
               Registered = str(round((totalRegistered/totalImages)*100)) + "%",
               StudyFound = True
             )
    if totalImages<0:
        return DicomStatusResponseSchema(Message =  "Run workflow query to get status.",
                                         StudyFound = True)
    return status
    
##  Create a new feed in CUBE with the provided params
##
##
##
##    
async def startFeed(params: dict) -> dict:
    pfdcm_name = params["pfdcm_name"]
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)
    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    cubeResource = params["cube_name"]
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cubeResource}/' 
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text)  
    
    ## Create a Chris Client
    cl = PythonChrisClient("http://localhost:8000/api/v1/","chris","chris1234")
    
    resp = cl.getFeed({"plugin_name" : "pl-dircopy", "title" : params["feed_name"]})
    if resp['total']>0:
        return {}
    ## Get the Swift path
    swiftSearchParams = {"name": params["dicomStudyUID"]}
    path = cl.getSwiftPath(swiftSearchParams)
    
    
    ## Get plugin Id 
    pluginSearchParams = {"name": params["plugin_name"]}   
    plugin_id = cl.getPluginId(pluginSearchParams)
    
    ## create a feed
    feedParams = {'title' : params["feed_name"],'dir' : path}
    feedResponse = cl.createFeed(plugin_id,feedParams)
    feed_id = feedResponse['id']
    
    ## Get pipeline id
    pipelineSearchParams = {'name':params["pipeline_name"]}
    pipeline_id = cl.getPipelineId(pipelineSearchParams)
    
    ## Create a workflow
    wfParams = {'previous_plugin_inst_id':feed_id, 'title' : params["feed_name"]}
    wfResponse = cl.createWorkflow(pipeline_id, wfParams)
    
    return wfResponse
