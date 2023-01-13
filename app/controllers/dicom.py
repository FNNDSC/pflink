import motor.motor_asyncio
from bson.objectid import ObjectId
import requests
import json

from controllers.pfdcm import (
    retrieve_pfdcm,
    retrieve_pfdcms,
)

        
# Get a 'hello' response from pfdcm
async def hello_pfdcm() -> dict:
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_hello_api = f'{pfdcm_url}/api/v1/hello/'
    
    response = requests.get(pfdcm_hello_api)
    d_results = json.loads(response.text)
    return d_results

# Get details about pfdcm
async def about_pfdcm() -> dict:
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_about_api = f'{pfdcm_url}/api/v1/about/'
    
    response = requests.get(pfdcm_about_api)
    d_results = json.loads(response.text)
    return d_results
    
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
    return d_results  
    
async def run_dicom_workflow(dicom : dict) -> dict:
    await dicom_do("retrieve",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
    await dicom_do("push",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
    await dicom_do("register",dicom.StudyInstanceUID,dicom.SeriesInstanceUID)
    return []

# Retrieve/push/register a dicom using pfdcm (WIP)
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
