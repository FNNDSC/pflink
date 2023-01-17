from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder

from controllers.cube import (
    add_cube,
    retrieve_cube,
    retrieve_cubes,
)
from models.cube import (
    CubeSchema,
    CubeGetModel,
    CubePutModel,
)

router = APIRouter()


@router.get(
    "/",
    response_description="cube setup info",
    summary="GET CUBE setup info like url and port",
    
)
async def get_cube():
    cubes = await retrieve_cubes()
    if cubes:
        return CubeGetModel(cubes, "cubes data retrieved successfully")
    return CubeGetModel(cubes, "Empty list returned")

@router.post("/", response_description="cube data added into the database")
async def add_cube_data(cube: CubeSchema = Body(...)):
    cube = jsonable_encoder(cube)
    new_cube = await add_cube(cube)
    return CubePutModel(new_cube)

@router.get("/{service_name}", response_description="pfdcm data retrieved")
async def get_cube_data(service_name):
    cube = await retrieve_cube(service_name)
    if cube:
        return CubeGetModel(cube, "cube data retrieved successfully")
    return ErrorResponseModel("An error occurred.", 404, "cube doesn't exist.")




