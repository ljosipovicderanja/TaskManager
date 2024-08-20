from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio

app = FastAPI()

services = {
    "task_service": "http://localhost:8001",
    "user_service": "http://localhost:8002",
    "notification_service": "http://localhost:8003",
    "backup_service": "http://localhost:8004"
}

class ServiceStatus(BaseModel):
    status: str

async def check_service_health(client, service_name, url):
    try:
        response = await client.get(f"{url}/health")
        if response.status_code == 200:
            return {service_name: "UP"}
        else:
            return {service_name: "DOWN"}
    except:
        return {service_name: "DOWN"}

@app.get("/services/health")
async def check_services_health():
    async with httpx.AsyncClient() as client:
        tasks = [check_service_health(client, name, url) for name, url in services.items()]
        results = await asyncio.gather(*tasks)
    return {k: v for result in results for k, v in result.items()}

@app.get("/")
async def read_root():
    return {"message": "Welcome to Task Management System"}

@app.get("/tasks")
async def get_tasks():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{services['task_service']}/tasks")
        return response.json()

@app.get("/users")
async def get_users():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{services['user_service']}/users")
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
