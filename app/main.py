from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routes.basic import router as BasicRouter
from app.routes.pfdcm import router as PfdcmRouter
from app.routes.workflow import router as WorkflowRouter
from app.routes.testing import router as WorkflowTestRouter
from app.routes.auth import router as AuthRouter
from app.routes.cube import router as CubeRouter
from app.config import settings
from app.controllers import auth
from logging.config import dictConfig
from app.models.log import LogConfig
from app.log_config import log_config

description = """
`pflink` is an application to interact with `CUBE` and `pfdcm` 🚀

User can **Query**/**Retrieve**/**Push**/**Register** dicoms and additionally create new feed, 
add new node or pipeline on the registered dicoms in CUBE using pflink.

## pfdcm

You can **add**,**retrieve** `pfdcm` service info.
Additionally you can:

* **Get a `hello` response from a pfdcm instance.**
* **Know `about` a pfdcm instance.**
* **Get the list of the names of all `cube` services available in a pfdcm instance.**
* **Get the list of the names of all `storage` services available in a pfdcm instance.**
* **Get the list of the names of all `PACS` services available in a pfdcm instance.**

## Workflow

You can **create** new workflows and get status of the workflow.

## Testing

You will be able to:

* **Get all workflow records present in the DB.**
* **Submit a test workflow request and get its simulated status in response.**

## Basic Auth

Create access tokens for user 

"""

tags_metadata = [
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
        "description": "Create dummy workflow records and get updated **status**. You can also **retrieve** all "
                       "the records from DB"
    }
]

#dictConfig(LogConfig().dict())
dictConfig(log_config)

app = FastAPI(
    title='pflink',
    version=settings.version,
    contact={"name": "FNNDSC", "email": "dev@babymri.org"},
    openapi_tags=tags_metadata,
    description=description
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(BasicRouter, tags=["Basic Info"], prefix="/api/v1")
app.include_router(PfdcmRouter, tags=["Pfdcm Service Info"], prefix="/api/v1/pfdcm",
                   dependencies=[Depends(auth.get_current_user)])
app.include_router(WorkflowRouter, tags=["Workflow Services"], prefix="/api/v1/workflow",
                   dependencies=[Depends(auth.get_current_user)])
app.include_router(WorkflowTestRouter, tags=["Test Workflow Services"], prefix="/api/v1/testing")
app.include_router(AuthRouter, tags=["Basic Auth"], prefix="/api/v1/auth-token")
app.include_router(CubeRouter, tags=["Cube services"], prefix="/api/v1/cube")
