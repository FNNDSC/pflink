import motor.motor_asyncio
import requests
import json
import concurrent.futures
from controllers.client.PythonChrisClient import PythonChrisClient
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

def workflow_status(
    pfdcm_url : str,
    dicom     : dict,
) -> dict:
    """
    Return the status of a workflow in `pflink`
    """
    # Ask `pfdcm` for study
    pfdcm_resp = get_pfdcm_status(pfdcm_url,dicom)
    
    # Ask `CUBE` for feed
    cube_resp = get_feed_status(pfdcm_resp,dicom)
    
    # Parse both the respones
    workflow_response = parse_response(pfdcm_resp, cube_resp)
    
    # return the response
    return workflow_response


 
    
async def threaded_workflow_do(dicom:dict, pfdcm_url:str) -> Future:
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(threadpool, run_workflow, dicom, pfdcm_url)
    return future
     
                      
def run_workflow(dicom:dict, pfdcm_url:str):
    asyncio.run(run_dicom_workflow(dicom,pfdcm_url))
    
async def run_dicom_workflow(dicom:dict, pfdcm_url:str) -> dict: 
    task = asyncio.create_task(run_dicom_workflow_do(dicom,pfdcm_url))
    await task

                                              
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
    cubeResource = dicom.thenArgs.CUBE
    pfdcm_smdb_cube_api = f'{pfdcm_url}/api/v1/SMDB/CUBE/{cubeResource}/' 
    response = requests.get(pfdcm_smdb_cube_api)
    d_results = json.loads(response.text)  
   
    
    ## Create a Chris Client
    client = do_cube_create_user("http://localhost:8000/api/v1/",dicom.feedArgs.User)
    
    ## Get the Swift path
    swiftSearchParams = {"StudyInstanceUID": dicom.StudyInstanceUID,"SeriesInstanceUID" : dicom.SeriesInstanceUID}
    dataPath = client.getSwiftPath(swiftSearchParams)
    
    response = workflow_status(pfdcm_url, dicom)
    if response.StudyFound:
        while not response.WorkflowStarted:
            if response.StudyRetrieved:
                if response.StudyPushed:
                    if response.StudyRegistered:
                        if response.FeedCreated:
                            feedId = response.FeedId
                            print(feedId)
                            workflowName = response.FeedName
                            # Check if user runs a new pipeline or node
                            if dicom.feedArgs.Pipeline:
                                do_cube_create_workflow(client,dicom.feedArgs.Pipeline,feedId,workflowName)
                            else:
                                do_cube_create_node(client,nodeArgs,feedId)
                        # wait and create a feed
                        print("Creating a feed")
                        feed_id = do_cube_create_feed(client,"new-feed-$$",dataPath)
                        print(feed_id)
                    # wait and register study
                    do_pfdcm_register(dicom,pfdcm_url)
                # wait and push study
                do_pfdcm_push(dicom,pfdcm_url)
            # wait and retrieve study
            do_pfdcm_retrieve(dicom,pfdcm_url)
           
            # wait here for n seconds b4 polling again
            time.sleep(2)
            response = workflow_status(pfdcm_url, dicom)

    # return immediately as study cannot be found
    return response
    
    
    
### HELPER METHODS ###

### PFDCM SPECIFIC METHODS ###
def get_pfdcm_status(pfdcm_url,dicom):
    """
    Get the status of PACS from `pfdcm`
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

   
def pfdcm_do(verb : str,thenArgs:dict,dicom : dict, url : str) -> dict:
    """
    # A reusable method to either retrieve, push or register dicoms using pfdcm
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

### CUBE SPECIFIC METHODS ###    
def get_feed_status(pfdcmResponse: dict, dicom: dict):
    """
    Get the status of a feed inside `CUBE`
    """
    feedName = dicom.feedArgs.FeedName
    d_dicom = pfdcmResponse['pypx']['data']
    if d_dicom:
        feedName = parseFeedTemplate(feedName, d_dicom[0])        
    if feedName == "":
        feedName = "/*/"
        
    cubeResponse = {
        "FeedName" : "",
        "FeedCreated" : False,
        "FeedProgress" : "",
        "WorkflowStarted": False,
        "FeedStatus" : "",
        "FeedError" : "",
        "FeedId" : ""}
        
    cl = PythonChrisClient("http://localhost:8000/api/v1/","chris","chris1234")   
    resp = cl.getFeed({"plugin_name" : "pl-dircopy", "title" : feedName})
    if resp['total']>0:
        cubeResponse['FeedCreated'] = True
        cubeResponse['FeedName'] = resp['data'][0]['title']
        cubeResponse['FeedId'] = resp['data'][0]['id']
        wfResp = cl.getWorkflow({"title" : feedName})
        print(resp['data'][0])
        if wfResp['total']>0:
            cubeResponse['WorkflowStarted'] = True
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
            cubeResponse['FeedProgress'] = str (round(finishedNodes/(len(instResp['data']) + 1)*100)) + "%"
            if finishedNodes == len(instResp['data']) + 1:
                feedStatus = "Completed"
            cubeResponse['FeedStatus'] = feedStatus
            cubeResponse['FeedError'] = feedError
            
    return cubeResponse
    
    
def do_cube_create_feed(client,feedName,dataPath):
    """
    Create a new feed in `CUBE` if not already present
    """
    # check if feed already present
    resp = client.getFeed({"plugin_name" : "pl-dircopy", "title" : feedName})
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
        print(resp)
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
            
    
def do_cube_create_node():
    """
    Create a new node (plugin instance) on an existing feed in `CUBE`
    """
    pass
    
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


def parseFeedTemplate(feedTemplate : str, dcmData : dict) -> str:
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
    


def parse_response(pfdcmResponse : dict, cubeResponse : dict ) -> dict:
    """
    Parse JSON object for status
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
        status.FeedCreated = cubeResponse['FeedCreated']
        status.FeedId = cubeResponse['FeedId']
        status.FeedName = cubeResponse['FeedName']
        status.FeedProgress = cubeResponse['FeedProgress']
        status.WorkflowStarted = cubeResponse['WorkflowStarted']
        status.FeedStatus = cubeResponse['FeedStatus']
        status.Error = cubeResponse['FeedError']
        
        
    return status
