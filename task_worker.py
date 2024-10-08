import json
from fastapi import FastAPI, HTTPException
import httpx
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from database import tasks_collection, users_collection

with open("config.json") as config_file:
    config = json.load(config_file)

app = FastAPI()

#Configurable parameters from config.jso
task_worker_host = config["task_worker_host"]
task_worker_port = config["task_worker_port"]


# Model za Task
class Task(BaseModel):
    title: str
    description: str
    status: str = "pending"
    user_id: Optional[str] = None  

# Model za ažuriranje Task-a
class UpdateTaskModel(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]
    user_id: Optional[str]  

@app.post("/tasks/", response_model=dict)
async def create_task(task: Task):
    # Provjera formata user_id
    if not ObjectId.is_valid(task.user_id):
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    
    # Provjera postojanja korisnika s danim user_id
    user = await users_collection.find_one({"_id": ObjectId(task.user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User with given ID does not exist")

    # Ako je user_id validan, kreiraj zadatak
    task_dict = task.dict()
    result = await tasks_collection.insert_one(task_dict)

    # Slanje obavijesti korisniku putem notification_service
    notification_data = {
        "user_id": task.user_id,
        "message": f"Novi zadatak kreiran: {task.title}",
        "read": False
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            notification_response = await client.post(f"http://127.0.0.1:8003/notifications/", json=notification_data)
            notification_response.raise_for_status()  # Provjeri je li obavijest uspješno poslana
    except httpx.HTTPStatusError as e:
        print(f"Failed to send notification: {e}")
        # Ovdje možete odlučiti kako dalje, npr. obrisati kreirani zadatak ili samo nastaviti

    return {"id": str(result.inserted_id)}


# Dohvaćanje svih zadataka
@app.get("/tasks/", response_model=List[Task])
async def get_tasks():
    tasks = await tasks_collection.find().to_list(100)
    return tasks

# Dohvaćanje zadatka prema ID-u
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await tasks_collection.find_one({"_id": ObjectId(task_id)})
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Dohvaćanje zadataka prema korisniku
@app.get("/tasks/user/{user_id}", response_model=List[Task])
async def get_tasks_by_user(user_id: str):
    tasks = await tasks_collection.find({"user_id": user_id}).to_list(100)
    return tasks

# Ažuriranje zadatka prema ID-u
@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task: UpdateTaskModel):
    update_data = {k: v for k, v in task.dict().items() if v is not None}
    result = await tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or no change detected")
    return await get_task(task_id)

# Brisanje zadatka prema ID-u
@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    result = await tasks_collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

# Health Check ruta
@app.get("/health")
async def health_check():
    return {"status": "OK"}

@app.get("/")
async def read_root():
    return {"message": "Welcome to Task Management System"}

# Pokretanje aplikacije
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=task_worker_host, port=task_worker_port)