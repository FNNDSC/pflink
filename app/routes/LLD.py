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
        
@router.post("/inputImage/{image_number}",response_description="Input image recieved")
async def get_input_image(
    data         : DicomStatusQuerySchema,
    image_number : str,
) -> FileResponse: 
    """
    Get an input image : Specify a number between 1-10
    """    
    return FileResponse(path=getcwd()  + f"/app/tests/inputImages/{image_number}.dcm")
    
@router.post("/imageWithHeatmaps/{image_number}",response_description="Image with heatmap downloaded")
async def get_image_with_heatmaps(
    data         : DicomStatusQuerySchema,
    image_number : str,
) -> FileResponse: 
    """
    Get an image with heatmaps : Specify a number between 1-10
    """   
    return FileResponse(path=getcwd()  + f"/app/tests/imageWithHeatmaps/{image_number}.jpg")
    
@router.post("/imageWithMeasurements/{image_number}",response_description="Image with measurements downloaded")
async def get_image_with_measurements(
    data         : DicomStatusQuerySchema,
    image_number : str,
) -> FileResponse: 
    """
    Get an image with measurements : Specify a number between 1-10
    """  
    return FileResponse(path=getcwd()  + f"/app/tests/imageWithMeasurements/{image_number}.png")
    
@router.post("/outputImage/{image_number}",response_description="Output image recieved")
async def get_output_image(
    data         : DicomStatusQuerySchema,
    image_number : str,
) -> FileResponse: 
    """
    Get an output image : Specify a number between 1-10
    """    
    return FileResponse(path=getcwd()  + f"/app/tests/outputImages/{image_number}.dcm")
