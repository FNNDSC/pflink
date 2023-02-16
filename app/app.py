from fastapi import FastAPI
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from routes.pfdcm import router as PfdcmRouter
from routes.basic import router as BasicRouter
from routes.workflow import router as WorkflowRouter
from controllers.pfdcm import add_pfdcm

    
app = FastAPI(
    title = 'pflink',
    version  = '1.0.0'
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(BasicRouter, tags=["Basic Information"], prefix="")
app.include_router(PfdcmRouter, tags=["Pfdcm Service Info "], prefix="/pfdcm")
app.include_router(WorkflowRouter, tags=["Workflow Services"], prefix="/workflow")



