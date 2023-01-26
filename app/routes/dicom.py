from fastapi import APIRouter, Body
import asyncio

from models.dicom import (
    DicomStatusQuerySchema,
    DicomActionQuerySchema,
    PACSqueyReturnModel,
)
from controllers.dicom import (
    dicom_status,
    run_dicom_workflow,
    threaded_workflow_do,
)

from controllers.pfdcm import (
    retrieve_pfdcm,
)

router = APIRouter()

@router.post("/status/", response_description="Status of a dicom")
async def post_dicom(dicom: DicomStatusQuerySchema = Body(...)):
    pfdcm_name = dicom.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    response = dicom_status(dicom,pfdcm_url)
    return PACSqueyReturnModel(response=response)
    
@router.post("/do/", response_description="Retrieve/push/register dicom")   
async def post_do_dicom(dicom : DicomActionQuerySchema = Body(...)):
    pfdcm_name = dicom.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    #response = await run_dicom_workflow(dicom,pfdcm_url)
    #return PACSqueyReturnModel(response=response)
    response = await threaded_workflow_do(dicom,pfdcm_url)
    return {}



