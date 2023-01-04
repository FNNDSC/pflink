from fastapi import  APIRouter, Query,FastAPI
from pydantic   import BaseModel, Field
from typing     import Optional, List, Tuple
from routes.dicom import router as DicomRouter
from models.basic import helloRouter_create
    
app = FastAPI()

app.include_router(DicomRouter, tags=["Dicom"], prefix="/dicom")

# /hello dependencies
# these modules provide some information on the host
# system/environment
import platform
import psutil
import multiprocessing
import os
import socket

### Basic Info Routes ### 
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to pflink app!"}
    
@app.get("/hello/", tags=["Hello"])
async def read_hello():
    return {"message": "Hello! from pflink"}

@app.get("/about/", tags=["About"])
async def read_about():
    return helloRouter_create("pflink","App to communicate with pfdcm and CUBE","1.0.0")



