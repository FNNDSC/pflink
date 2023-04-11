from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from controllers.pfdcm import (
    add_pfdcm,
    retrieve_pfdcm,
    retrieve_pfdcms,
    hello_pfdcm,
    about_pfdcm,
    
)
from models.pfdcm import (
    PfdcmSchema,
    PfdcmQuerySchema,
    PfdcmGetModel,
    PfdcmPutModel,
    ErrorResponseModel,
    PfdcmQueryReturnModel,
)

router = APIRouter()


@router.get(
    "/",
    response_description="pfdcm setup info",
    summary             = "Retrieve all `pfdcm` services saved"
)
async def get_pfdcms():
    """
    Fetch all `pfdcm` service addresses and ports
    """
    pfdcms = await retrieve_pfdcms()
    if pfdcms:
        return PfdcmGetModel(pfdcms, "pfdcm data retrieved successfully")
    return PfdcmGetModel(pfdcms, "Empty list returned")

    
@router.post(
    "/",
    response_description="pfdcm data added into the database",
    summary             = "Add new `pfdcm` service details"
)
async def add_pfdcm_data(pfdcm: PfdcmSchema = Body(...)):
    """
    Add service details like name, IP and port of a `pfdcm` instance
    """
    pfdcm = jsonable_encoder(pfdcm)
    new_pfdcm = await add_pfdcm(pfdcm)
    return PfdcmPutModel(new_pfdcm)


@router.get(
    "/{service_name}", 
    response_description="pfdcm data retrieved",
    summary             = "Get details for a `pfdcm` service"
)
async def get_pfdcm_data(service_name):
    """
    Fetch details like server IP and port from the DB for an existing service name 
    """
    pfdcm = await retrieve_pfdcm(service_name)
    if pfdcm:
        return PfdcmGetModel(pfdcm, "pfdcm data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, f"Service {service_name} doesn't exist in the DB.")
    
    
@router.post(
    "/hello/", 
    response_description="Hello from PFDCM",
    summary             = "Get a 'hello' response from a PFDCM instance"
)
async def get_hello_pfdcm(pfdcm : PfdcmQuerySchema = Body(...)):
    """
    Get a response from a specific `pfdcm` instance by providing its service name
    """
    response = await hello_pfdcm(pfdcm)
    return PfdcmQueryReturnModel(response=response)
    
    
@router.post(
    "/about/", 
    response_description="About PFDCM"
)
async def get_about_pfdcm(pfdcm : PfdcmQuerySchema = Body(...)):
    response = await about_pfdcm(pfdcm)
    return PfdcmQueryReturnModel(response=response)




