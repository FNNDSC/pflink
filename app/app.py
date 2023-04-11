from fastapi import FastAPI
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from routes.pfdcm import router as PfdcmRouter
from routes.basic import router as BasicRouter
from routes.workflow import router as WorkflowRouter
from routes.LLD import router as LLDRouter
from tests.test_workflow_route import router as WorkflowTestRouter
from config import settings

description = """
`pflink` is an application to interact with `CUBE` and `pfdcm` 🚀

User can **Query**/**Retrieve**/**Push**/**Register** dicoms and additionally create new feed, 
add new node or pipeline on the registered dicoms in CUBE using pflink.

## pfdcm

You can **add**,**retrieve** `pfdcm` service info.

## Workflows

You can **create** new workflows and get status of the workflow.

## LLD

You will be able to:

* **Get Input Image** (_test only_).
* **Get Image with Heatmaps** (_test only_).
* **Get Image with Measurements** (_test only_).
* **Get Output Image** (_test only_).
"""

tags_metadata    = [
    {
        "name": "Basic Info",
        "description": "Basic information of `pflink` like **hello** and **about**"
    },
    {
        "name": "Pfdcm Service Info",
        "description": "Service information of various `pfdcm` instances"
    },
    {
        "name": "Workflow Services",
        "description": "POST a request to create new workflows in `CUBE` and get **status** of a workflow"
    },
    {
        "name": "Test Workflow Services",
        "description": "Create dummy workflow records and get updated **status**. You can also **retrieve** and **delete** all dummy records in the DB"
    },
    {
        "name": "LLD Specific Services",
        "description": "Get different types of image file like **input images**, **heatmap images** and **output images** from a `LLD` workflow"
    }
]
    
app = FastAPI(
    title         = 'pflink',
    version       = settings.version,
    contact       = {
                        "name"  : "FNNDSC",
                        "email" : "dev@babymri.org"
                    },
    openapi_tags  = tags_metadata,
    description   = description
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
app.include_router(BasicRouter, tags=["Basic Info"], prefix="")
app.include_router(PfdcmRouter, tags=["Pfdcm Service Info"], prefix="/pfdcm")
app.include_router(WorkflowRouter, tags=["Workflow Services"], prefix="/workflow")
app.include_router(WorkflowTestRouter, tags=["Test Workflow Services"], prefix="/testing")
app.include_router(LLDRouter, tags=["LLD Specific Services"], prefix="/LLD")



