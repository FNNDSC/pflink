from fastapi import FastAPI

from routes.dicom import router as DicomRouter
from routes.pfdcm import router as PfdcmRouter
from routes.cube import router as CubeRouter
from routes.info import router as InfoRouter

    
app = FastAPI()

app.include_router(InfoRouter, tags=["Info"], prefix="")
app.include_router(DicomRouter, tags=["Dicom"], prefix="/dicom")
app.include_router(PfdcmRouter, tags=["Pfdcm"], prefix="/pfdcm")
app.include_router(CubeRouter, tags=["Cube"], prefix="/cube")




