from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://lartemuseums:ca7oPe2VJ1RphE5d@cluster0.ft15t.mongodb.net/"

client = AsyncIOMotorClient(MONGO_URI)
db = client.task_database

tasks_collection = db.tasks
users_collection = db.users
notifications_collection = db.notifications
backups_collection = db.backups
logs_collection = db.logs  