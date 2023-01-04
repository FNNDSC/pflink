from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from database import (
    retrieve_pfdcm,
)
from models.pfdcm import (
    PfdcmSchema,
    PfdcmGetModel,
    PfdcmPutModel,
)

router = APIRouter()


@router.get("/", response_description="pfdcm setup info")
async def get_pfdcm():
    pfdcm = await retrieve_pfdcm()
    if pfdcm:
        return PfdcmGetModel(pfdcm, "Dicoms data retrieved successfully")
    return PfdcmGetModel(pfdcm, "Empty list returned")






