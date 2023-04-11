from fastapi import APIRouter, Body
from fastapi.encoders import jsonable_encoder
from models.basic import helloRouter_create
from config import settings

router = APIRouter()


### Basic Info Routes ### 
@router.get("/")
async def read_root():
    return {"message": "Welcome to pflink app!"}
    
@router.get("/hello/")
async def read_hello():
    return {"message": "Hello! from pflink"}

@router.get("/about/")
async def read_about():
    return helloRouter_create("pflink","App to communicate with pfdcm and CUBE",settings.version)






