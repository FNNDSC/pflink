from fastapi import APIRouter, Body, HTTPException
from app.controllers import cube

router = APIRouter()


@router.get(
    "/plugin/list",
    status_code=200,
    response_description="Plugin list retrieved successfully.",
    summary="Get a list of plugins registered to a CUBE instance.",
)
async def get_plugins(pfdcm_name: str, cube_name: str) -> list:
    """
    Get a list of plugins registered to a CUBE instance.
    """
    resp = cube.get_plugins(pfdcm_name, cube_name)
    return resp


@router.get(
    "/pipeline/list",
    status_code=200,
    response_description="Pipeline list retrieved successfully.",
    summary="Get a list of pipelines registered to a CUBE instance.",
)
async def get_pipelines(pfdcm_name: str, cube_name: str) -> dict:
    """
    Get a list of pipelines registered to a CUBE instance.
    """
    resp = cube.get_pipelines(pfdcm_name, cube_name)
    return resp