import motor.motor_asyncio
from bson.objectid import ObjectId

MONGO_DETAILS = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.dicoms

student_collection = database.get_collection("dicoms_collection")

# helpers


def dicom_helper(student) -> dict:
    return {
        "seriesID": dicom["seriesID"],
        "studyID": dicom["studyID"],

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


# Retrieve a dicom with a matching ID
async def retrieve_dicom(seriesID: str) -> dict:
    dicom = await dicom_collection.find_one({"_id": ObjectId(seriesID)})
    if dicom:
        return dicom_helper(dicom)



