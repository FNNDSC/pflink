from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from controllers.pfdcm import (
    add_pfdcm,
    retrieve_pfdcm,
    retrieve_pfdcms,
    
)
from models.pfdcm import (
    PfdcmSchema,
    PfdcmGetModel,
    PfdcmPutModel,
    ErrorResponseModel,
)

router = APIRouter()


@router.get("/", response_description="pfdcm setup info")
async def get_pfdcms():
    pfdcms = await retrieve_pfdcms()
    if pfdcms:
        return PfdcmGetModel(pfdcms, "pfdcm data retrieved successfully")
    return PfdcmGetModel(pfdcms, "Empty list returned")
    
@router.post("/", response_description="pfdcm data added into the database")
async def add_pfdcm_data(pfdcm: PfdcmSchema = Body(...)):
    pfdcm = jsonable_encoder(pfdcm)
    new_pfdcm = await add_pfdcm(pfdcm)
    return PfdcmPutModel(new_pfdcm)

@router.get("/{service_name}", response_description="pfdcm data retrieved")
async def get_pfdcm_data(service_name):
    pfdcm = await retrieve_pfdcm(service_name)
    if pfdcm:
        return PfdcmGetModel(pfdcm, "pfdcm data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, "Dicom doesn't exist.")






