from fastapi import APIRouter, Body, BackgroundTasks
import asyncio

from models.workflow import (
    DicomStatusQuerySchema,
    DicomActionQuerySchema,
    PACSqueyReturnModel,
    DicomStatusResponseSchema,
)
from controllers.workflow import (
    workflow_status,
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
    response = workflow_status(pfdcm_url,dicom)
    return PACSqueyReturnModel(response=response)
    
@router.post("/do/", response_description="Retrieve/push/register dicom")   
async def post_do_dicom( 
    background_tasks: BackgroundTasks, 
    dicom : DicomActionQuerySchema = Body(...)
):
    pfdcm_name = dicom.PFDCMservice
    pfdcm_server = await retrieve_pfdcm(pfdcm_name)    
    pfdcm_url = pfdcm_server['server_ip'] + ":" +pfdcm_server['server_port']
    background_tasks.add_task(threaded_workflow_do,dicom,pfdcm_url)
    return DicomStatusResponseSchema(FeedName = dicom.feedArgs.FeedName,
                                     Message = "POST the same request replacing the API endpoint with /status/ to get the status") 



