from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from database import db
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# Model za zadatke
class Task(BaseModel):
    title: str
    description: str
    completed: bool = False

    class Config:
        schema_extra = {
            "example": {
                "title": "Finish FastAPI project",
                "description": "Complete CRUD operations",
                "completed": False
            }
        }

class UpdateTaskModel(BaseModel):
    title: Optional[str]
    description: Optional[str]
    completed: Optional[bool]

    class Config:
        schema_extra = {
            "example": {
                "title": "Update the FastAPI project",
                "description": "Fix bugs in CRUD operations",
                "completed": True
            }
        }

# CRUD operacije za zadatke
@app.post("/tasks/", response_model=dict)
async def create_task(task: Task):
    task_dict = task.dict()
    result = await db.tasks.insert_one(task_dict)
    return {"id": str(result.inserted_id)}

@app.get("/tasks/", response_model=List[Task])
async def get_tasks():
    tasks = await db.tasks.find().to_list(100)
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await db.tasks.find_one({"_id": ObjectId(task_id)})
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task: UpdateTaskModel):
    update_data = {k: v for k, v in task.dict().items() if v is not None}
    result = await db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return await get_task(task_id)

@app.delete("/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

@app.get("/health/")
async def health_check():
    return {"status": "OK"}

@app.get("/")
def read_root():
    return {"message": "Hello, World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
