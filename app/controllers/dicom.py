import motor.motor_asyncio
from bson.objectid import ObjectId
import requests
import json
from controllers.PythonChrisClient import PythonChrisClient
from datetime import datetime


from controllers.pfdcm import (
    retrieve_pfdcm,
    retrieve_pfdcms,
)
from models.dicom import (
    DicomStatusResponseSchema,
)

    
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
    if exists:
        return parseResponse(exists[0][dicom.StudyInstanceUID][0]['images'])
    return DicomStatusResponseSchema(Message = "Study not found.",
                                     StudyFound = False)
    
 
# Retrieve/push/register a dicom using pfdcm (WIP)   
async def run_dicom_workflow(dicom : dict) -> dict:   
    ## Step 1:
    ## Step 2:
    ## Step 3:
    await dicom_do("retrieve",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
    await dicom_do("push",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
    await dicom_do("register",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
    
    ## Step 4: Create a feed on registered PACS files
    current_dateTime = datetime.now()
    feedName = "pflink-" + dicom.SeriesInstanceUID + "-" + dicom.cubeArgs.App + str(current_dateTime)
    feedParams = {"dicomStudyUID" : dicom.StudyInstanceUID,
                  "pipeline_name" : dicom.cubeArgs.Pipeline,
                  "plugin_name"   : "pl-dircopy",
                  "feed_name"     : feedName}
    
    response = startFeed(feedParams)
    return response

### Helper Methods ###
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
def startFeed(params: dict) -> dict:

    ## Create a Chris Client
    cl = PythonChrisClient()
    
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
    wfParams = {'previous_plugin_inst_id':feed_id}
    wfResponse = cl.createWorkflow(pipeline_id, wfParams)
    
    return wfResponse
