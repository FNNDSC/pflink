from fastapi import FastAPI

from routes.pfdcm import router as PfdcmRouter
from routes.cube import router as CubeRouter
from routes.info import router as InfoRouter
from routes.dicom import router as DicomRouter

    
app = FastAPI(
    title = 'pflink',
    version  = '1.0.0'
)

app.include_router(InfoRouter, tags=["Info"], prefix="")
app.include_router(PfdcmRouter, tags=["Pfdcm"], prefix="/pfdcm")
app.include_router(CubeRouter, tags=["Cube"], prefix="/cube")
app.include_router(DicomRouter, tags=["Dicom"], prefix="/dicom")



