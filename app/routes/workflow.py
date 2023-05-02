from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBearer, HTTPBasic
from app.controllers import workflow
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
)
from app.config import user

security = HTTPBasic()
router = APIRouter()


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user.user_name = credentials.username
    user.password = credentials.password
    return True


@router.post(
    "",
    response_description="Workflow response retrieved",
    summary="Create a workflow",
    dependencies=[Depends(authenticate_user)]
)
async def create_workflow(data: WorkflowRequestSchema) -> WorkflowStatusResponseSchema:
    """
    Get the status of a workflow by POSTing a payload using this API endpoint.
    If it's the first time a client is POSTing a payload, this API creates a new
    entry in the DB and returns a default response.
    """  
    response = await workflow.post_workflow(data)
    return response

