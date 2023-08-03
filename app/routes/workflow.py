from fastapi import APIRouter
from app.controllers import workflow
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
)
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
    response = await workflow.post_workflow(data)
    return response


@router.get("/list", response_description="All workflows retrieved")
async def get_workflows():
    """
    Fetch all workflows currently present in the database
    """
    workflows = workflow.retrieve_workflows()
    return workflows


@router.delete("", response_description="All workflows deleted")
async def delete_workflows():
    """
    Delete all workflow records from the prod database table
    """
    response = await workflow.delete_workflows()
    return response