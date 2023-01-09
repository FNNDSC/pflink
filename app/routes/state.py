from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder
import requests
from models.state import (
    PACSqueyReturnModel,
    ResponseModel,
)
from controllers.pfdcm import (
    retrieve_pfdcms,
)



router = APIRouter()


@router.get("/{mrn}", response_description="Just some example JSON")
async def get_dicom(mrn):
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_dicom_api = f'{pfdcm_url}/api/v1/dicom/?mrn={mrn}'
    x = requests.get(pfdcm_dicom_api)
    return PACSqueyReturnModel(response=x.text)

@router.get("/hello/", response_description="Hello from PFDCM")
async def get_hello_pfdcm():
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_hello_api = f'{pfdcm_url}/api/v1/hello/'
    x = requests.get(pfdcm_hello_api)
    return PACSqueyReturnModel(response=x.text)

@router.get("/about/", response_description="About PFDCM")
async def get_about_pfdcm():
    pfdcm_list = []
    pfdcm_list = await retrieve_pfdcms()
    
    pfdcm_url = pfdcm_list[0]['server_ip'] + ":" + pfdcm_list[0]['server_port']
    pfdcm_about_api = f'{pfdcm_url}/api/v1/about/'
    x = requests.get(pfdcm_about_api)
    return PACSqueyReturnModel(response=x.text)



