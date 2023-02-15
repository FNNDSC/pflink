from fastapi import APIRouter

from models.workflow import (
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
)

from controllers.workflow import (
    post_workflow,
    retrieve_workflows,
)

router = APIRouter()
    
@router.get("/",response_description="All workflows retrieved")
async def get_workflows():
    workflows = await retrieve_workflows()
    return workflows
    
@router.post("/",response_description="Workflow response retrieved")
async def create_workflow(data : DicomStatusQuerySchema) -> DicomStatusResponseSchema:   
    response = await post_workflow(data)   
    return response
