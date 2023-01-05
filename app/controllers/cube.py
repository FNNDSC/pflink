import motor.motor_asyncio
from bson.objectid import ObjectId


MONGO_DETAILS = "mongodb://localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)

database = client.cubes

cube_collection = database.get_collection("cubes_collection")


# helpers


def cube_helper(cube) -> dict:
    return {
        "id": str(cube["_id"]),
        "service_name": cube["service_name"],
        "server_ip"   : cube["server_ip"],
        "server_port" : cube["server_port"],
    }

# Retrieve all cube present in the database
async def retrieve_cubes():
    cubes = []
    async for cube in cube_collection.find():
        cubes.append(cube_helper(cube))
    return cubes


# Add a new cube into to the database
async def add_cube(cube_data: dict) -> dict:
    cube = await cube_collection.insert_one(cube_data)
    new_cube = await cube_collection.find_one({"_id": cube.inserted_id})
    return cube_helper(new_cube)


# Retrieve a cube with a matching service name
async def retrieve_cube(service_name: str) -> dict:
    cube = await cube_collection.find_one({"service_name": service_name})
    if cube:
        return cube_helper(cube)
