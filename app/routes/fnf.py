from fastapi import APIRouter, Body, BackgroundTasks

from controllers.fnf import (
    update_status,
    post_workflow,
    manage_workflow,
    retrieve_workflows,
)

from models.fnf import (
    FnfRequestSchema,
    FnfStatusSchema,
)

router = APIRouter()

@router.get("/",response_description="All workflows retrieved")
async def get_workflows():
    workflows = await retrieve_workflows()
    return workflows
    
@router.post("/",response_description="POST new workflow request")
async def create_workflow(background_tasks:BackgroundTasks, data:FnfRequestSchema) ->FnfStatusSchema:
    response = await post_workflow(data)
    background_tasks.add_task(update_status,response["key"])
    background_tasks.add_task(manage_workflow,response["key"])
    return response["status"]
