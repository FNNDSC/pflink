import motor.motor_asyncio
import requests
import json
from controllers.client.PythonChrisClient import PythonChrisClient
#from controllers.AnotherChrisClient import AIOChrisClient
from datetime import datetime
import time
from    concurrent.futures  import  ThreadPoolExecutor, Future
import asyncio
from controllers.pfdcm import (
    retrieve_pfdcm,
)
from models.workflow import (
    DicomStatusResponseSchema,
)

threadpool      = ThreadPoolExecutor()

def workflow_status(
    pfdcm_url : str,
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
    workflow_response = parse_response(pfdcm_resp, cube_resp)
    
    # return the response
    return workflow_response
 

                                              
async def threaded_workflow_do(dicom:dict, pfdcm_url:str) -> dict:
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
    client = do_cube_create_user("http://localhost:8000/api/v1/",dicom.feedArgs.User)
    
    response = workflow_status(pfdcm_url, dicom)
    if response.StudyFound:
        pfdcmResponse = get_pfdcm_status(pfdcm_url,dicom)
        feedName = dicom.feedArgs.FeedName
        d_dicom = pfdcmResponse['pypx']['data']
        feedName = parseFeedTemplate(feedName, d_dicom[0])

        while not response.WorkflowStarted and MAX_RETRIES>0:
            if not response.Retrieved == "0%":
                if not response.Pushed == "0%":
                    if not response.Registered == "0%":
                        if response.FeedCreated:
                        
                            # Get previous inst Id
                            pluginInstSearchParams = {'plugin_name' : 'pl-dircopy', 'feed_id' : response.FeedId}
                            pvInstId = client.getPluginInstances(pluginInstSearchParams)['data'][0]['id']
                            workflowName = response.FeedName
                            
                            # Check if user runs a new pipeline or node
                            if dicom.feedArgs.Pipeline:
                                print("adding pipeline")
                                do_cube_create_workflow(client,dicom.feedArgs.Pipeline,pvInstId,workflowName)
                            else:
                                print("adding new node")
                                do_cube_create_node(client,dicom.feedArgs,pvInstId)
                        else:        
                            # wait and create a feed
                            print("Creating a feed")
                        
                            ## Get the Swift path
                            dataPath = client.getSwiftPath(dicom.PACSdirective)
                            if feedName=="":
                               raise Exception("Please enter a valid feed name.") 
                            feed_id = do_cube_create_feed(client,feedName,dataPath)
                    else:    
                        # wait and register study
                        print("registering study")
                        do_pfdcm_register(dicom,pfdcm_url)
                else: 
                    print("pushing study")   
                    # wait and push study
                    do_pfdcm_push(dicom,pfdcm_url)
            else: 
                print("retrieveing study")   
                # wait and retrieve study
                do_pfdcm_retrieve(dicom,pfdcm_url)
           
            # wait here for n seconds b4 polling again
            print("sleeping for 2 seconds")
            await asyncio.sleep(2)
            response = workflow_status(pfdcm_url, dicom)
            MAX_RETRIES -= 1
            
        #end of while loop
        return response
    else:
        # return immediately as study cannot be found
        return response
    
    
    
### HELPER METHODS ###

### PFDCM SPECIFIC METHODS ###
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
        
    cubeResponse = {
        "FeedName" : "",
        "FeedCreated" : False,
        "FeedProgress" : "Not started",
        "WorkflowStarted": False,
        "FeedStatus" : "",
        "FeedError" : "",
        "FeedId" : ""}
        
    feedName = dicom.feedArgs.FeedName
    d_dicom = pfdcmResponse['pypx']['data']
    if d_dicom:
        feedName = parseFeedTemplate(feedName, d_dicom[0])        
    if feedName == "":
        cubeResponse['FeedError'] = "Please enter a valid feed name"
        
    cl = do_cube_create_user("http://localhost:8000/api/v1/",dicom.feedArgs.User)   
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
        status.FeedCreated = cubeResponse['FeedCreated']
        status.FeedId = cubeResponse['FeedId']
        status.FeedName = cubeResponse['FeedName']
        status.FeedProgress = cubeResponse['FeedProgress']
        status.WorkflowStarted = cubeResponse['WorkflowStarted']
        status.FeedStatus = cubeResponse['FeedStatus']
        status.Error = cubeResponse['FeedError']
        
        
    return status
