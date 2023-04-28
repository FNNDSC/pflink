from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBearer

from app.controllers.workflow import (
    post_workflow,
)
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
)

security = HTTPBearer()
router = APIRouter()


@router.post(
    "",
    response_description="Workflow response retrieved",
    summary="Create a workflow",
)
async def create_workflow(data: WorkflowRequestSchema) -> WorkflowStatusResponseSchema:
    """
    Get the status of a workflow by POSTing a payload using this API endpoint.
    If it's the first time a client is POSTing a payload, this API creates a new
    entry in the DB and returns a default response.
    """  
    response = await post_workflow(data)   
    return response

