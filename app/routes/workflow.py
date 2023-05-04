from fastapi import APIRouter, Depends
from app.controllers import workflow
from app.controllers.auth import get_current_user
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
)
router = APIRouter()


@router.post(
    "",
    response_description="Workflow response retrieved",
    summary="Create a workflow",
    dependencies=[Depends(get_current_user)]
)
async def create_workflow(data: WorkflowRequestSchema) -> WorkflowStatusResponseSchema:
    """
    Get the status of a workflow by POSTing a payload using this API endpoint.
    If it's the first time a client is POSTing a payload, this API creates a new
    entry in the DB and returns a default response.
    """
    response = await workflow.post_workflow(data)
    return response


