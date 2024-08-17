#Konfiguracija MongoDb Atlas kolekcije
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://lartemuseums:ca7oPe2VJ1RphE5d@cluster0.ft15t.mongodb.net/"
client = AsyncIOMotorClient(MONGO_URI)
db = client.get_database("task_database")
