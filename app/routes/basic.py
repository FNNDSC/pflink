from fastapi import APIRouter, Body
from models.basic import AboutModel
from config import settings

router = APIRouter()


# Basic Info Routes
@router.get("/")
async def read_root():
    return {"message": "Welcome to pflink app!"}


@router.get("/hello")
async def read_hello():
    """
    Get a hello response from `pflink`
    """
    return {"message": "Hello! from pflink"}


@router.get("/about")
async def read_about():
    """
    Get details about `pflink`
    """
    return AboutModel(
               name="pflink",
               about="App to communicate with pfdcm and CUBE",
               version=settings.version)
