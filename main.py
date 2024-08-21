import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio

#Loading the configuration from config.json
with open("config.json") as config_file:
    config = json.load(config_file)

app = FastAPI()

#Configurable parameters from config.json
main_host = config["main_host"]
main_port = config["main_port"]
task_worker_host = config["task_worker_host"]
task_worker_port = config["task_worker_port"]
user_service_host = config["user_service_host"]
user_service_port = config["user_service_port"]
notification_service_host = config["notification_service_host"]
notification_service_port = config["notification_service_port"]
health_check_service_host = config["health_check_service_host"]
health_check_service_port = config["health_check_service_port"]
task_backup_host = config["task_backup_host"]
task_backup_port = config["task_backup_port"]


services = {
    "task_worker": "http://localhost:8001",
    "user_service": "http://localhost:8002",
    "notification_service": "http://localhost:8003",
    "health_check_service": "http://localhost:8004",
    "task_backup": "http://localhost:8005"
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
    
@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=main_host, port=main_port)