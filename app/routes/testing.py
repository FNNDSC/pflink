from fastapi import APIRouter
from app.models.workflow import (
    WorkflowRequestSchema,
    WorkflowStatusResponseSchema,
)
from app.controllers import workflow
router = APIRouter()


@router.post("", response_description="Status response retrieved")
async def test_create_workflow(
        data: WorkflowRequestSchema,
        error_type: str | None = None,
) -> WorkflowStatusResponseSchema:
    """
    Use this API to test how `pflink` creates new workflows and updates
    different states of a workflow in the DB.
    A client can get various states of a workflow life-cycle by POSTing the
    same request again and again.
    You can pass an optional `?error_type={error_type}` to get a run-time error.
     A valid `error_type` would be one of these values:
     * **pfdcm**
     * **study**
     * **feed**
     * **analysis**
     * **compute**
     * **cube**

     For an invalid error_type you get an error message as follows:
      * "Undefined error_type : Please pass values as pfdcm/study/feed/analysis/compute/cube as valid error_type"
    """
    response = await workflow.post_workflow(data, test=True, error_type=error_type)
    return response


@router.get("/list", response_description="All workflows retrieved")
async def test_get_workflows():
    """
    Fetch all workflows currently present in the database
    """
    workflows = workflow.retrieve_workflows()
    return workflows


