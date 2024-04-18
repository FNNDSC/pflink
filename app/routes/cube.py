from fastapi import APIRouter, Body, HTTPException, Response, status
from app.controllers import cube
from app.models import cube
from typing import List

router = APIRouter()


@router.get("",
            status_code=200,
            response_description="CUBE details retrieved successfully.",
            summary="Get the details like service address of an existing CUBE service."
            )
async def get_cube_service_details(cube_name: str, response: Response) -> dict:
    """Get request to fetch CUBE service details"""
    try:
        raise Exception("Method not implemented")
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})


@router.get("/list",
            status_code=200,
            response_description="CUBE list retrieved successfully.",
            summary="Get a list of CUBE services added to this `pflink` instance."
            )
async def get_all_cubes(response: Response) -> List[str]:
    """Get request to fetch all CUBE services configured in pflink"""
    try:
        raise Exception("Method not implemented")
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})


@router.post("",
             status_code=201,
             response_description="New CUBE service added successfully.",
             summary="""Add a new CUBE service to `pflink`.
                        Ensure that the service name of CUBE matches an existing
                        `pfdcm` service name. Otherwise the system will throw validation errors."""
             )
async def add_cube_service(cube_data: cube.CubeService, response: Response) -> dict:
    """ Add a new CUBE service details to pflink"""
    try:
        raise Exception("Method not implemented")
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})


@router.put("",
            status_code=200,
            response_description="CUBE details updated successfully.",
            summary="Update an existing CUBE service endpoints."
            )
async def update_cube_service(cube_data: cube.CubeService, response: Response) -> dict:
    """Update the service endpoints of an existing CUBE resource"""
    try:
        raise Exception("Method not implemented")
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})


@router.delete("",
               status_code=202,
               response_description="CUBE service deleted successfully.",
               summary="Delete an existing CUBE service added to this `pflink` service"
               )
async def delete_cube_service(cube_name: str, response: Response) -> dict:
    """Delete an existing CUBE service"""
    try:
        raise Exception("Method not implemented")
    except Exception as ex:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTTPException(status_code=404, detail={"error": str(ex)})
