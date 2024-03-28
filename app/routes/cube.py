from fastapi import APIRouter, Body, HTTPException, Response, status
from app.controllers import cube

router = APIRouter()


@router.get(
    "/plugin/list",
    response_description="Plugin list retrieved successfully.",
    summary="Get a list of plugins registered to a CUBE instance.",
)
async def get_plugins(pfdcm_name: str, cube_name: str, response: Response) -> list:
    """
    Get a list of plugins registered to a CUBE instance.
    """
    try:
        resp = await cube.get_plugins(pfdcm_name, cube_name)
        return resp
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})


@router.get(
    "/pipeline/list",
    status_code=200,
    response_description="Pipeline list retrieved successfully.",
    summary="Get a list of pipelines registered to a CUBE instance.",
)
async def get_pipelines(pfdcm_name: str, cube_name: str, response: Response) -> dict:
    """
    Get a list of pipelines registered to a CUBE instance.
    """
    try:
        resp = cube.get_pipelines(pfdcm_name, cube_name)
        return resp
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})