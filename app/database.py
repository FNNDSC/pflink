import motor.motor_asyncio
from bson.objectid import ObjectId


MONGO_DETAILS = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.dicoms

dicom_collection = database.get_collection("dicoms_collection")


# helpers


def dicom_helper(dicom) -> dict:
    return {
        "id": str(dicom["_id"]),
        "series_id": dicom["series_id"],
        "study_id": dicom["study_id"],
    }

# Retrieve all dicoms present in the database
async def retrieve_dicoms():
    dicoms = []
    async for dicom in dicom_collection.find():
        dicoms.append(dicom_helper(dicom))
    return dicoms


# Add a new dicom into to the database
async def add_dicom(dicom_data: dict) -> dict:
    dicom = await dicom_collection.insert_one(dicom_data)
    new_dicom = await dicom_collection.find_one({"_id": dicom.inserted_id})
    return dicom_helper(new_dicom)


# Retrieve a dicom with a matching SeriesUID
async def retrieve_dicom(series_id: str) -> dict:
    dicom = await dicom_collection.find_one({"series_id": series_id})
    if dicom:
        return dicom_helper(dicom)




