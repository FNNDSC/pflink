from fastapi import APIRouter

from models.workflow import (
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
)

from controllers.workflow import (
    post_workflow,
)

router = APIRouter()
        
@router.post(
    "/",
    response_description="Workflow response retrieved",
    summary             = "Create a workflow")
async def create_workflow(data : DicomStatusQuerySchema) -> DicomStatusResponseSchema: 
    """
    Get the status of a workflow by POSTing a payload using this API endpoint.
    If it's the first time a client is POSTing a payload, this API creates a new
    entry in the DB and returns a default response.
    """  
    response = await post_workflow(data)   
    return response
