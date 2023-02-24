from fastapi import APIRouter

from models.workflow import (
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
)

from controllers.workflow import (
    post_workflow,
    retrieve_workflows,
    delete_workflows,
)

router = APIRouter()
    
@router.get("/",response_description="All workflows retrieved")
async def test_get_workflows():
    """
    Fetch all workflows currently present in the database
    """
    workflows = await retrieve_workflows()
    return workflows
    
@router.post("/",response_description="Status response retrieved")
async def test_create_workflow(
    data         : DicomStatusQuerySchema,
) -> DicomStatusResponseSchema:
    """
    Use this API to test how `pflink` creates new workflows and updates
    different states of a workflow in the DB.
    A client can get various states of a workflow life-cycle by POSTing the
    same request again and again
    """  
    response = await post_workflow(data,test=True)   
    return response
    
@router.delete("/",response_description="All workflows deleted")
async def delete_all():
    """
    Delete all records: 
    # USE ONLY ON A TEST SETUP
    """
    response = await delete_workflows()
    return response
