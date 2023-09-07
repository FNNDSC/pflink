from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from app.controllers import pfdcm
from app.models.pfdcm import (
    PfdcmQuerySchema,
    PfdcmQueryResponseSchema,
)

router = APIRouter()


@router.post(
    "",
    status_code=201,
    response_description="pfdcm data added into the database.",
    summary="Add new `pfdcm` service details.",
)
async def add_pfdcm_data(pfdcm_data: PfdcmQuerySchema = Body(...)) -> PfdcmQueryResponseSchema:
    """
    Add service details like name and address of a `pfdcm` instance.
    """
    pfdcm_data = jsonable_encoder(pfdcm_data)
    new_pfdcm = await pfdcm.add_pfdcm(pfdcm_data)
    if new_pfdcm.get("error"):
        raise HTTPException(status_code=400, detail=new_pfdcm["error"])
    return PfdcmQueryResponseSchema(data=new_pfdcm, message="New record created.")


@router.get(
    "/list",
    response_description="pfdcm setup info.",
    summary="Retrieve all `pfdcm` services saved."
)
async def get_pfdcms() -> list[str]:
    """
    Fetch all `pfdcm` service addresses from the DB.
    """
    pfdcms = await pfdcm.retrieve_pfdcms()
    return pfdcms


@router.get(
    "/{service_name}", 
    response_description="pfdcm data retrieved.",
    summary="Get address of a `pfdcm` service."
)
async def get_pfdcm_data(service_name: str) -> PfdcmQueryResponseSchema:
    """
    Fetch service address of a pfdcm instance from the DB for an existing service name.
    """
    pfdcm_data = pfdcm.retrieve_pfdcm(service_name)
    if pfdcm_data:
        return PfdcmQueryResponseSchema(data=pfdcm_data, message="pfdcm data retrieved successfully.")
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
    response = await pfdcm.hello_pfdcm(service_name)
    if response.get("error"):
        raise HTTPException(status_code=502, detail=response["error"])
    return PfdcmQueryResponseSchema(data=response, message='')
    
    
@router.get(
    "/{service_name}/about",
    response_description="About PFDCM",
    summary="Get details about a `pfdcm` instance"
)
async def get_about_pfdcm(service_name: str) -> PfdcmQueryResponseSchema:
    """
    Get details about a specific `pfdcm` instance by providing its service name
    """
    response = await pfdcm.about_pfdcm(service_name)
    if response.get("error"):
        raise HTTPException(status_code=502, detail=response["error"])
    return PfdcmQueryResponseSchema(data=response, message='')


@router.get(
    "/{service_name}/cube/list",
    response_description="About PFDCM",
    summary="Get the list of cube services registered to a `pfdcm` instance"
)
async def cube_service_list(service_name: str) -> list[str]:
    """
    Get the list of CUBE services registered to a `pfdcm` instance by providing its service name
    """
    response = await pfdcm.cube_list(service_name)
    if not response:
        raise HTTPException(status_code=502, detail=f"Unable to reach endpoints of {service_name}")
    return response


@router.get(
    "/{service_name}/storage/list",
    response_description="About PFDCM",
    summary="Get the list of storage services registered to a `pfdcm` instance"
)
async def storage_service_list(service_name: str) -> list[str]:
    """
    Get the list of storage services registered to a `pfdcm` instance by providing its service name
    """
    response = await pfdcm.storage_list(service_name)
    if not response:
        raise HTTPException(status_code=502, detail=f"Unable to reach endpoints of {service_name}")
    return response


@router.get(
    "/{service_name}/PACSservice/list",
    response_description="About PFDCM",
    summary="Get the list of PACS services registered to a `pfdcm` instance"
)
async def pacs_service_list(service_name: str) -> list[str]:
    """
    Get the list of PACS services registered to a `pfdcm` instance by providing its service name
    """
    response = await pfdcm.pacs_list(service_name)
    if not response:
        raise HTTPException(status_code=502, detail=f"Unable to reach endpoints of {service_name}")
    return response


@router.delete("", response_description="pfdcm record deleted")
async def delete_pfdcm(service_name: str):
    """
    Delete a pfdcm record from the DB
    """
    response = await pfdcm.delete_pfdcm(service_name)
    return response
