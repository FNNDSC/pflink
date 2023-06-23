from fastapi import APIRouter, Body, HTTPException
from app.controllers import cube

router = APIRouter()


@router.get(
    "/plugin/list",
    status_code=200,
    response_description="pfdcm data added into the database.",
    summary="Add new `pfdcm` service details.",
)
async def get_plugins(pfdcm_name: str, cube_name: str) -> list:
    """
    Add service details like name and address of a `pfdcm` instance.
    """
    resp = cube.get_plugins(pfdcm_name, cube_name)
    return resp


@router.get(
    "/pipeline/list",
    status_code=200,
    response_description="pfdcm data added into the database.",
    summary="Add new `pfdcm` service details.",
)
async def get_pipelines(pfdcm_name: str, cube_name: str) -> dict:
    """
    Add service details like name and address of a `pfdcm` instance.
    """
    resp = cube.get_pipelines(pfdcm_name, cube_name)
    return resp