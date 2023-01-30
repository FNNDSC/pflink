import motor.motor_asyncio
import requests
import json
import concurrent.futures
from controllers.PythonChrisClient import PythonChrisClient
#from controllers.AnotherChrisClient import AIOChrisClient
from datetime import datetime
import time
from    concurrent.futures  import  ThreadPoolExecutor, Future
import asyncio
from controllers.pfdcm import (
    retrieve_pfdcm,
)
from models.dicom import (
    DicomStatusResponseSchema,
)

threadpool      = ThreadPoolExecutor()


              
def dicom_data(dicom: dict, pfdcm_url:str) -> dict:
    '''
    Given a dictionary object containing relevant key-value pairs for a PACS query,
    return a dictionary object containing the details of DICOM series if present
    '''  

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
          "AccessionNumber": dicom.AccessionNumber,
          "PatientID": dicom.PatientID,
          "PatientName": dicom.PatientName,
          "PatientBirthDate": dicom.PatientBirthDate,
          "PatientAge": dicom.PatientAge,
          "PatientSex": dicom.PatientSex,
          "StudyDate": dicom.StudyDate,
          "StudyDescription": dicom.StudyDescription,
          "StudyInstanceUID": dicom.StudyInstanceUID,
          "Modality": dicom.Modality,
          "ModalitiesInStudy": dicom.ModalitiesInStudy,
          "PerformedStationAETitle": dicom.PerformedStationAETitle,
          "NumberOfSeriesRelatedInstances": dicom.NumberOfSeriesRelatedInstances,
          "InstanceNumber": dicom.InstanceNumber,
          "SeriesDate": dicom.SeriesDate,
          "SeriesDescription": dicom.SeriesDescription,
          "SeriesInstanceUID": dicom.SeriesInstanceUID,
          "ProtocolName": dicom.ProtocolName,
          "AcquisitionProtocolDescription": dicom.AcquisitionProtocolDescription,
          "AcquisitionProtocolName": dicom.AcquisitionProtocolName,
          "withFeedBack": True,
          "then": 'status',
          "thenArgs": "",
          "dblogbasepath": dicom.dblogbasepath,
          "json_response": True
        }
      }

    response = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    return json.loads(response.text)  
    

def dicom_status(dicom: dict, pfdcm_url:str) -> dict:
    '''
    Given a dictionary object containing relevant key-value pairs for a PFDCM query &
    CUBE query, return a dictionary object containing the details of status of a 
    workflow in `pflink`
    '''
    d_results = dicom_data(dicom, pfdcm_url) 
    exists =  d_results['pypx']['then']['00-status']['study']
    feedTemplate = dicom.feedArgs.FeedName

    dicomResponse = DicomStatusResponseSchema()
    d_dicom = d_results['pypx']['data']
    feedName = feedTemplate
    
        
    if exists:
        try:
            dicomResponse = parseResponse(exists[0][dicom.StudyInstanceUID][0]['images'])
        except:
            dicomResponse.Message = "Please specify details of the dicom"
    else:
        dicomResponse.Message = "Study not found"
    if d_dicom:
        feedName = parseFeedTemplate(feedTemplate, d_dicom[0])        
    if feedName == "":
        feedName = "/*/"
        
    cl = PythonChrisClient("http://localhost:8000/api/v1/","chris","chris1234")   
    resp = cl.getFeed({"plugin_name" : "pl-dircopy", "title" : feedName})
    if resp['total']>0:
        dicomResponse.FeedCreated = True
        dicomResponse.FeedName = resp['data'][0]['title']
        wfResp = cl.getWorkflow({"title" : feedName})
        if wfResp['total']>0:
            print(wfResp['total'])
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
                      
def run_workflow(dicom:dict, pfdcm_url:str):
    asyncio.run(run_dicom_workflow(dicom,pfdcm_url))
    
async def run_dicom_workflow(dicom:dict, pfdcm_url:str) -> dict: 
    task = asyncio.create_task(run_dicom_workflow_do(dicom,pfdcm_url))
    await task

    #return DicomStatusResponseSchema(FeedName = dicom.feedArgs.FeedName,
                                     #Message = "POST the same request replacing the API endpoint with /status/ to get the status")
                                     
async def threaded_workflow_do(dicom:dict, pfdcm_url:str) -> Future:
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(threadpool, run_workflow, dicom, pfdcm_url)
    return future
         
async def run_dicom_workflow_do(dicom:dict, pfdcm_url:str) -> dict:
    """
    Given a dictionary object containing key-value pairs for PFDCM query & CUBE
    query, return a dictionary object as response after completing a series of
    tasks. The sequence of tasks is as followa:
        1) Check if dicoms are already present in pfdcm
            a) if not, retrieve dicoms from PACS to pfdcm
        2) Push dicoms to CUBE swift storage
        3) Register dicoms to CUBE
        4) Create a new feed on the registered PACS files in CUBE
        5) Start a workflow specified by the used on top the newly created feed
    """
    print("here")
    response = dicom_status(dicom, pfdcm_url)
    
    while not response.WorkflowStarted:
        if response.StudyFound:
            dicom_do("retrieve",dicom,pfdcm_url)
        else:
            break
        if response.Retrieved == "100%":
            dicom_do("push",dicom,pfdcm_url)
        if response.Pushed == "100%":
            dicom_do("register",dicom,pfdcm_url)
        if response.Registered == "100%":
            dicomData = dicom_data(dicom,pfdcm_url)
            feedName = parseFeedTemplate(dicom.feedArgs.FeedName,dicomData['pypx']['data'][0])
            feedParams = {
                  "dicomSeriesUID": dicom.SeriesInstanceUID,
                  "dicomStudyUID" : dicom.StudyInstanceUID,
                  "pipeline_name" : dicom.feedArgs.Pipeline,
                  "plugin_name"   : "pl-dircopy",
                  "feed_name"     : feedName,
                  "pfdcm_name"    : dicom.PFDCMservice,
                  "cube_name"     : dicom.thenArgs.CUBE,
                  "user_name"     : dicom.feedArgs.User}
    
            response = startFeed(feedParams,pfdcm_url)
        time.sleep(2)
        response = dicom_status(dicom, pfdcm_url)
        print(response.WorkflowStarted)
    
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
    

# A reusable method to either retrieve, push or register dicoms using pfdcm   
def dicom_do(verb : str,dicom : dict, url : str) -> dict:
    if verb=="retrieve":
        thenArgs = ""
    elif verb == "push":

         thenArgs = {'db': dicom.thenArgs.db,
                     'swift': dicom.thenArgs.swift, 
                     'swiftServicesPACS': dicom.thenArgs.swiftServicesPACS,
                     'swiftPackEachDICOM': dicom.thenArgs.swiftPackEachDICOM}
                   
    elif verb=="register":
        thenArgs = {
                     "db": dicom.thenArgs.db,
                     "CUBE": dicom.thenArgs.CUBE,
                     "swiftServicesPACS": dicom.thenArgs.swiftServicesPACS,
                     "parseAllFilesWithSubStr": dicom.thenArgs.parseAllFilesWithSubStr
                   }
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
             "AccessionNumber": dicom.AccessionNumber,
             "PatientID": dicom.PatientID,
             "PatientName": dicom.PatientName,
             "PatientBirthDate": dicom.PatientBirthDate,
             "PatientAge": dicom.PatientAge,
             "PatientSex": dicom.PatientSex,
             "StudyDate": dicom.StudyDate,
             "StudyDescription": dicom.StudyDescription,
             "StudyInstanceUID": dicom.StudyInstanceUID,
             "Modality": dicom.Modality,
             "ModalitiesInStudy": dicom.ModalitiesInStudy,
             "PerformedStationAETitle": dicom.PerformedStationAETitle,
             "NumberOfSeriesRelatedInstances": dicom.NumberOfSeriesRelatedInstances,
             "InstanceNumber": dicom.InstanceNumber,
             "SeriesDate": dicom.SeriesDate,
             "SeriesDescription": dicom.SeriesDescription,
             "SeriesInstanceUID": dicom.SeriesInstanceUID,
             "ProtocolName": dicom.ProtocolName,
             "AcquisitionProtocolDescription": dicom.AcquisitionProtocolDescription,
             "AcquisitionProtocolName": dicom.AcquisitionProtocolName,
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
def startFeed(params: dict, pfdcm_url : str) -> dict:
    
    cubeResource = params["cube_name"]
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cubeResource}/' 
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text)  
    
    
    create_user_api = "http://localhost:8000/api/v1/users/"
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
             "username" : params["user_name"],
             "password" : params["user_name"] +"1234",
             "email"    :  params["user_name"]+"@email.com",
             }
    resp = requests.post(create_user_api,json=myobj,headers=headers)
    
    ## Create a Chris Client
    cl = PythonChrisClient("http://localhost:8000/api/v1/",params["user_name"],params["user_name"] +"1234")
    #cl = PythonChrisClient("http://localhost:8000/api/v1/","chris","chris1234")
    resp = cl.getFeed({"plugin_name" : "pl-dircopy", "title" : params["feed_name"]})
    print(resp['total'])
    if resp['total']>0:
        return {}
    ## Get the Swift path
    swiftSearchParams = {"StudyInstanceUID": params["dicomStudyUID"],"SeriesInstanceUID" : params["dicomSeriesUID"]}
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
    print(pipeline_id)
    ## Create a workflow
    wfParams = {'previous_plugin_inst_id':feed_id, 'title' : params["feed_name"]}
    wfResponse = cl.createWorkflow(pipeline_id, wfParams)
    
    return wfResponse

async def get_pfdcm_status():
    pass    
async def do_pfdcm_retrieve():
    pass
async def do_pfdcm_push():
    pass
async def do_pfdcm_register():
    pass
async def do_cube_create_feed():
    pass
async def do_cube_create_workflow():
    pass
async def do_cube_create_node():
    pass
    
