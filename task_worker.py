from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from database import tasks_collection, notifications_collection  
from datetime import datetime

app = FastAPI()

class Task(BaseModel):
    title: str
    description: str
    status: str = "pending"
    user_id: str  

class UpdateTaskModel(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]
    user_id: Optional[str] 

async def create_notification(user_id: str, message: str):
    notification = {
        "user_id": user_id,
        "message": message,
        "read": False,
        "timestamp": datetime.utcnow(),
    }
    await notifications_collection.insert_one(notification)

@app.post("/tasks/", response_model=dict)
async def create_task(task: Task):
    task_dict = task.dict()
    result = await tasks_collection.insert_one(task_dict)
    await create_notification(task.user_id, f"Zadatak '{task.title}' je kreiran.")
    return {"id": str(result.inserted_id)}

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task: UpdateTaskModel):
    update_data = {k: v for k, v in task.dict().items() if v is not None}
    result = await tasks_collection.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or no change detected")
    updated_task = await get_task(task_id)
    await create_notification(updated_task.user_id, f"Zadatak '{updated_task.title}' je ažuriran.")
    return updated_task

@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    task = await get_task(task_id)  # Dohvaćamo zadatak prije brisanja
    result = await tasks_collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    await create_notification(task.user_id, f"Zadatak '{task.title}' je obrisan.")
    return {"message": "Task deleted successfully"}

# Health Check ruta
@app.get("/health")
async def health_check():
    return {"status": "OK"}

# Pokretanje aplikacije
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)