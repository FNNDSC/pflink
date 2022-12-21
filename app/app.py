from fastapi import FastAPI

from routes.dicom import router as DicomRouter

app = FastAPI()

app.include_router(DicomRouter, tags=["Dicom"], prefix="/dicom")


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to pflink app!"}


