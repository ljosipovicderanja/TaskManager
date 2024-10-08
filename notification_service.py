from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from database import notifications_collection
from motor.motor_asyncio import AsyncIOMotorClient
import json

with open("config.json") as config_file:
    config = json.load(config_file)

app = FastAPI()

#Configurable parameters from config.jso
notification_service_host = config["notification_service_host"]
notification_service_port = config["notification_service_port"]

class Notification(BaseModel):
    user_id: str
    message: str
    read: bool = False

@app.post("/notifications/", response_model=dict)
async def create_notification(notification: Notification):
    notification_dict = notification.dict()
    result = await notifications_collection.insert_one(notification_dict)
    return {"id": str(result.inserted_id)}

@app.get("/notifications/", response_model=List[Notification])
async def get_notifications():
    notifications = await notifications_collection.find().to_list(100)
    return notifications

@app.get("/notifications/{user_id}", response_model=List[Notification])
async def get_user_notifications(user_id: str):
    notifications = await notifications_collection.find({"user_id": user_id}).to_list(100)
    return notifications

@app.put("/notifications/{notification_id}", response_model=Notification)
async def mark_notification_as_read(notification_id: str):
    result = await notifications_collection.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found or already marked as read")
    return await notifications_collection.find_one({"_id": ObjectId(notification_id)})

@app.get("/notifications/unread/{user_id}", response_model=List[Notification])
async def get_unread_notifications(user_id: str):
    notifications = await notifications_collection.find({"user_id": user_id, "read": False}).to_list(100)
    return notifications

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=notification_service_host, port=notification_service_port)