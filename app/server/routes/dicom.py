from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from app.server.database import (
    add_dicom,
    retrieve_dicom,
    retrieve_dicoms,

)
from app.server.models.dicom import (
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

