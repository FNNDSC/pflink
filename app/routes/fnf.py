from fastapi import APIRouter, Body, BackgroundTasks

from controllers.fnf import (
    post_workflow,
)

from models.fnf import (
    FnfSchema,
    FnfResponseSchema,
)

router = APIRouter()


@router.post("/api/v1/", response_description="post a workflow")
async def run_workflow(background_tasks: BackgroundTasks,request: FnfSchema = Body(...)) ->dict:
    response = await post_workflow( background_tasks,request)
    return response
