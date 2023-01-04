from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from controllers.dicom import (
    add_dicom,
    retrieve_dicom,
    retrieve_dicoms,
)
from models.dicom import (
    ErrorResponseModel,
    ResponseModel,
    DicomSchema,
    UpdateDicomModel,
)

router = APIRouter()

@router.post("/", response_description="Dicom data added into the database")
async def add_dicom_data(dicom: DicomSchema = Body(...)):
    dicom = jsonable_encoder(dicom)
    new_dicom = await add_dicom(dicom)
    return ResponseModel(new_dicom, "Dicom added successfully.")

@router.get("/", response_description="Dicoms retrieved")
async def get_dicoms():
    dicoms = await retrieve_dicoms()
    if dicoms:
        return ResponseModel(dicoms, "Dicoms data retrieved successfully")
    return ResponseModel(dicoms, "Empty list returned")


@router.get("/{series_id}", response_description="Dicom data retrieved")
async def get_dicom_data(series_id):
    dicom = await retrieve_dicom(series_id)
    if dicom:
        return ResponseModel(dicom, "Dicom data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, "Dicom doesn't exist.")



