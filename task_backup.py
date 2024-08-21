from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from database import backupscollection
from motor.motorasyncio import AsyncIOMotorClient
import json

with open("config.json") as configfile:
    config = json.load(configfile)

app = FastAPI()

#Configurable parameters from config.jso
task_backup_host = config["task_backup_host"]
task_backup_port = config["task_backup_port"]

class Task(BaseModel):
    title: str
    description: str
    status: str = "pending"

class User(BaseModel):
    username: str
    email: str

@app.post("/backup/tasks/", response_model=dict)
async def backup_task(task: Task):
    task_dict = task.dict()
    result = await backups_collection.insert_one({"type": "task", "data": task_dict})
    return {"id": str(result.inserted_id)}

@app.get("/backup/tasks/", response_model=List[Task])
async def get_backup_tasks():
    tasks = await backups_collection.find({"type": "task"}).to_list(100)
    return [task["data"] for task in tasks]

@app.post("/backup/users/", response_model=dict)
async def backup_user(user: User):
    user_dict = user.dict()
    result = await backups_collection.insert_one({"type": "user", "data": user_dict})
    return {"id": str(result.inserted_id)}

@app.get("/backup/users/", response_model=List[User])
async def get_backup_users():
    users = await backups_collection.find({"type": "user"}).to_list(100)
    return [user["data"] for user in users]

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name == "__main":
    import uvicorn
    uvicorn.run(app, host="task_backup_host", port=task_backup_port)