from fastapi import FastAPI

from routes.pfdcm import router as PfdcmRouter
from routes.cube import router as CubeRouter
from routes.basic import router as BasicRouter
from routes.dicom import router as DicomRouter

    
app = FastAPI(
    title = 'pflink',
    version  = '1.0.0'
)

app.include_router(BasicRouter, tags=["Basic Information"], prefix="")
app.include_router(PfdcmRouter, tags=["Pfdcm Service Addresses "], prefix="/pfdcm")
app.include_router(CubeRouter, tags=["Cube Service Addresses"], prefix="/cube")
app.include_router(DicomRouter, tags=["Dicom Services"], prefix="/dicom")



