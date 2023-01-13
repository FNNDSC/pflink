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
    hello_pfdcm,
    about_pfdcm,
    dicom_status,
    dicom_do,
)

router = APIRouter()


@router.get("/hello/", response_description="Hello from PFDCM")
async def get_hello_pfdcm():
    response = await hello_pfdcm()
    return PACSqueyReturnModel(response=response)

@router.get("/about/", response_description="About PFDCM")
async def get_about_pfdcm():
    response = await about_pfdcm()
    return PACSqueyReturnModel(response=response)

@router.post("/status/", response_description="Status of a dicom")
async def post_dicom(dicom: DicomStatusQuerySchema = Body(...)):
    response = await dicom_status(dicom)
    return PACSqueyReturnModel(response=response)
    
@router.post("/do={verb}/", response_description="Retrieve/push/register dicom")
async def post_dicom(verb,study_id,series_id):
    response = await dicom_do(verb,study_id,series_id)
    return PACSqueyReturnModel(response=response)

