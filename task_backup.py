from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from bson import ObjectId
from database import backups_collection, tasks_collection, users_collection, notifications_collection
import json
import socket
import uvicorn

# Učitavanje konfiguracije iz config.json
with open("config.json") as config_file:
    config = json.load(config_file)

app = FastAPI()

# Konfiguracija hosta i porta iz config.json
task_backup_host = config["task_backup_host"]
initial_port = config["task_backup_port"]

# Model za zadatke
class Task(BaseModel):
    title: str
    description: str
    status: str = "pending"
    user_id: Optional[str] = None 

# Model za korisnike
class User(BaseModel):
    username: str
    email: EmailStr

# Model za notifikacije
class Notification(BaseModel):
    user_id: str
    message: str
    read: bool = False

# Ruta za backup zadataka
@app.post("/backup/tasks/", response_model=dict)
async def backup_task(task: Task):
    task_dict = task.dict()
    result = await backups_collection.insert_one({"type": "task", "data": task_dict})
    return {"id": str(result.inserted_id)}

# Dohvaćanje backupiranih zadataka
@app.get("/backup/tasks/", response_model=List[Task])
async def get_backup_tasks():
    tasks = await backups_collection.find({"type": "task"}).to_list(100)
    return [task["data"] for task in tasks]

# Ruta za backup korisnika
@app.post("/backup/users/", response_model=dict)
async def backup_user(user: User):
    user_dict = user.dict()
    result = await backups_collection.insert_one({"type": "user", "data": user_dict})
    return {"id": str(result.inserted_id)}

# Dohvaćanje backupiranih korisnika
@app.get("/backup/users/", response_model=List[User])
async def get_backup_users():
    users = await backups_collection.find({"type": "user"}).to_list(100)
    return [user["data"] for user in users]

# Ruta za backup notifikacija
@app.post("/backup/notifications/", response_model=dict)
async def backup_notification(notification: Notification):
    notification_dict = notification.dict()
    result = await backups_collection.insert_one({"type": "notification", "data": notification_dict})
    return {"id": str(result.inserted_id)}

# Dohvaćanje backupiranih notifikacija
@app.get("/backup/notifications/", response_model=List[Notification])
async def get_backup_notifications():
    notifications = await backups_collection.find({"type": "notification"}).to_list(100)
    return [notification["data"] for notification in notifications]

# Health check ruta
@app.get("/health")
async def health_check():
    return {"status": "OK"}

# Funkcija za pronalaženje prvog slobodnog porta
def find_free_port(host, start_port):
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) != 0:
                return port
            port += 1

if __name__ == "__main__":
    import uvicorn
    port_to_use = find_free_port(task_backup_host, initial_port)
    uvicorn.run(app, host=task_backup_host, port=port_to_use)
