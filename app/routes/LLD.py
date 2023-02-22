from fastapi import APIRouter
from fastapi.responses import FileResponse
from os import getcwd

from models.workflow import (
    DicomStatusQuerySchema,
    DicomStatusResponseSchema,
)

from controllers.workflow import (
    post_workflow,
)

router = APIRouter()
        
@router.post("/inputImage",response_description="Input image recieved")
async def get_input_image(
    data : DicomStatusQuerySchema,
    name_file : str,
) -> FileResponse: 
    """
    """    
    return FileResponse(path=getcwd()  + "/images/workflow_do.png")
    
@router.post("/imageWithHeatmaps",response_description="Image with heatmap downloaded")
async def get_image_with_heatmaps(
    data : DicomStatusQuerySchema,
    name_file : str,
) -> FileResponse: 
    """
    """   
    return FileResponse(path=getcwd() + "/images/workflow_do.png", media_type='application/octet-stream', filename="test.png")
    
@router.post("/imageWithMeasurements",response_description="Image with measurements downloaded")
async def get_image_with_measurements(
    data : DicomStatusQuerySchema,
    name_file : str,
) -> FileResponse: 
    """
    """  
    return FileResponse(path=getcwd() + "/images/workflow_do.png" , media_type='application/octet-stream', filename="test.png")
