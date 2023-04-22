from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from app.controllers.pfdcm import (
    add_pfdcm,
    retrieve_pfdcm,
    retrieve_pfdcms,
    hello_pfdcm,
    about_pfdcm,
    pacs_list,
    swift_list,
    cube_list,
    
)
from app.models.pfdcm import (
    PfdcmQuerySchema,
    PfdcmQueryResponseSchema,
    PfdcmCollectionResponseModel,
)

router = APIRouter()


@router.get(
    "",
    response_description="pfdcm setup info.",
    summary="Retrieve all `pfdcm` services saved."
)
async def get_pfdcms() -> PfdcmCollectionResponseModel:
    """
    Fetch all `pfdcm` service addresses from the DB.
    """
    pfdcms = await retrieve_pfdcms()
    if pfdcms:
        return PfdcmCollectionResponseModel(data=pfdcms, message="pfdcm data retrieved successfully.")
    return PfdcmCollectionResponseModel(data=pfdcms, message="There are no records in the DB.")

    
@router.post(
    "",
    response_description="pfdcm data added into the database.",
    summary="Add new `pfdcm` service details."
)
async def add_pfdcm_data(pfdcm: PfdcmQuerySchema = Body(...)) -> PfdcmQueryResponseSchema:
    """
    Add service details like name and address of a `pfdcm` instance.
    """
    pfdcm = jsonable_encoder(pfdcm)
    new_pfdcm = await add_pfdcm(pfdcm)
    if not new_pfdcm:
        return PfdcmQueryResponseSchema(data={}, message=f"service_name must be unique."
                                                         f" {pfdcm['service_name']} already exists.")
    return PfdcmQueryResponseSchema(data=new_pfdcm, message="New record created.")


@router.get(
    "/{service_name}", 
    response_description="pfdcm data retrieved.",
    summary="Get address of a `pfdcm` service."
)
async def get_pfdcm_data(service_name: str) -> PfdcmQueryResponseSchema:
    """
    Fetch service address of a pfdcm instance from the DB for an existing service name.
    """
    pfdcm = retrieve_pfdcm(service_name)
    if pfdcm:
        return PfdcmQueryResponseSchema(data=pfdcm, message="pfdcm data retrieved successfully.")
    return PfdcmQueryResponseSchema(data=[], message=f"No existing record found for {service_name}.")
    
    
@router.get(
    "/{service_name}/hello",
    response_description="Hello from PFDCM",
    summary="Get a 'hello' response from a PFDCM instance"
)
async def get_hello_pfdcm(service_name: str) -> PfdcmQueryResponseSchema:
    """
    Get a hello response from a specific `pfdcm` instance by providing its service name
    """
    response = await hello_pfdcm(service_name)
    return PfdcmQueryResponseSchema(data=response, message="")
    
    
@router.get(
    "/{service_name}/about",
    response_description="About PFDCM",
    summary="Get details about a `pfdcm` instance"
)
async def get_about_pfdcm(service_name: str) -> PfdcmQueryResponseSchema:
    """
    Get details about a specific `pfdcm` instance by providing its service name
    """
    response = await about_pfdcm(service_name)
    return PfdcmQueryResponseSchema(data=response, message="")

@router.get(
    "/{service_name}/cube/list",
    response_description="About PFDCM",
    summary="Get details about a `pfdcm` instance"
)
async def cube_service_list(service_name: str) -> PfdcmCollectionResponseModel:
    """
    Get details about a specific `pfdcm` instance by providing its service name
    """
    response = await cube_list(service_name)
    return PfdcmCollectionResponseModel(data=response, message="")

@router.get(
    "/{service_name}/swift/list",
    response_description="About PFDCM",
    summary="Get details about a `pfdcm` instance"
)
async def swift_service_list(service_name: str) -> PfdcmCollectionResponseModel:
    """
    Get details about a specific `pfdcm` instance by providing its service name
    """
    response = await swift_list(service_name)
    return PfdcmCollectionResponseModel(data=response, message="")

@router.get(
    "/{service_name}/PACSservice/list",
    response_description="About PFDCM",
    summary="Get details about a `pfdcm` instance"
)
async def pacs_service_list(service_name: str) -> PfdcmCollectionResponseModel:
    """
    Get details about a specific `pfdcm` instance by providing its service name
    """
    response = await pacs_list(service_name)
    return PfdcmCollectionResponseModel(data=response, message="")
