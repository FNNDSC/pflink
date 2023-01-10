from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder
import requests
import json
from models.dicom import (
    PACSqueyReturnModel,
    ResponseModel,
)
from controllers.pfdcm import (
    retrieve_pfdcms,
)



router = APIRouter()


@router.get("/hello/", response_description="Hello from PFDCM")
async def get_hello_pfdcm():
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_hello_api = f'{pfdcm_url}/api/v1/hello/'
    x = requests.get(pfdcm_hello_api)
    d_results = json.loads(x.text)
    return PACSqueyReturnModel(response=d_results)

@router.get("/about/", response_description="About PFDCM")
async def get_about_pfdcm():
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_about_api = f'{pfdcm_url}/api/v1/about/'
    x = requests.get(pfdcm_about_api)
    d_results = json.loads(x.text)
    return PACSqueyReturnModel(response=d_results)

@router.post("/status/", response_description="Just some example JSON")
async def post_dicom(series_id,study_id):
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_dicom_api = f'{pfdcm_url}/api/v1/PACS/sync/pypx/'
    headers = {'Content-Type': 'application/json','accept': 'application/json'}
    myobj = {
  "PACSservice": {
    "value": 'orthanc'
  },
  "listenerService": {
    "value": "default"
  },
  "PACSdirective": {
    "SeriesInstanceUID": series_id,
    "StudyInstanceUID": study_id,
    "withFeedBack": False,
    "then": "status",
    "thenArgs": "",
    "dblogbasepath": '/home/dicom/log',
    "json_response": True
  }
}

    x = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    d_results = json.loads(x.text)
    return PACSqueyReturnModel(response=d_results["pypx"]["then"]["00-status"])
    
@router.post("/do={verb}/", response_description="Just some example JSON")
async def post_dicom(verb,series_id,study_id):
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
    "SeriesInstanceUID": series_id,
    "StudyInstanceUID": study_id,
    "withFeedBack": False,
    "then": verb,
    "thenArgs": "{\"db\":\"/home/dicom/log\",\"swift\":\"local\",\"CUBE\":\"local\",\"swiftServicesPACS\":\"orthanc\",\"parseAllFilesWithSubStr\":\"dcm\"}",
    "dblogbasepath": '/home/dicom/log',
    "json_response": True
  }
}

    x = requests.post(pfdcm_dicom_api, json = myobj, headers=headers)
    d_results = json.loads(x.text)
    return PACSqueyReturnModel(response=d_results)

