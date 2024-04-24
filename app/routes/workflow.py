from fastapi import APIRouter, Body
from app.controllers import workflow
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
    WorkflowSearchSchema,
)
import datetime
from app.controllers.subprocesses import utils
from typing import Annotated

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


@router.get("/search", response_description="All workflows retrieved")
async def get_workflows(
    keywords: str = ""
):
    """
    Fetch all workflows currently present in the database matching the search criteria
    """
    search_params = WorkflowSearchSchema(
    keywords = keywords,
    )
    workflows = workflow.retrieve_workflows(search_params)
    return workflows
    
    
@router.get("", response_description="Workflow retrieved successfully")
async def get_workflow(workflow_key: str):
    """
    Fetch workflow recorded by using hash of a request.
    """
    workflow = utils.retrieve_workflow(workflow_key)
    return workflow


@router.delete("", response_description="Selected workflow deleted successfully")
async def delete_workflow(workflow_key: str):
    """
    Delete a single workflow record from the prod database table
    """
    response = await workflow.delete_workflow(workflow_key)
    return response

@router.get("/date_search")
async def get_workflows_by_date(
        start_date: datetime.date=datetime.date.today(),
        end_date: datetime.date=datetime.date.today()):
    return workflow.search_workflows_by_date(start_date, end_date)
