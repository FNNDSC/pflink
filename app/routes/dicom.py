from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder
import requests
import json
from models.dicom import (
    DicomStatusQuerySchema,
    DicomActionQuerySchema,
    PACSqueyReturnModel,
    ResponseModel,
)
from controllers.dicom import (
    dicom_status,
    run_dicom_workflow,
)

router = APIRouter()

@router.post("/status/", response_description="Status of a dicom")
async def post_dicom(dicom: DicomStatusQuerySchema = Body(...)):
    response = await dicom_status(dicom)
    return PACSqueyReturnModel(response=response)
    
@router.post("/do/", response_description="Retrieve/push/register dicom")
async def post_dicom(dicom : DicomActionQuerySchema = Body(...)):
    response = await run_dicom_workflow(dicom)
    return PACSqueyReturnModel(response=response)

