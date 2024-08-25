import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import subprocess
import os

# Loading the configuration from config.json
with open("config.json") as config_file:
    config = json.load(config_file)

app = FastAPI()

# Configurable parameters from config.json
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
    "task_worker": f"http://{task_worker_host}:{task_worker_port}",
    "user_service": f"http://{user_service_host}:{user_service_port}",
    "notification_service": f"http://{notification_service_host}:{notification_service_port}",
    "health_check_service": f"http://{health_check_service_host}:{health_check_service_port}",
    "task_backup": f"http://{task_backup_host}:{task_backup_port}"
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

@app.get("/tasks/")
async def get_tasks():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{services['task_worker']}/tasks/")
            response.raise_for_status()  # Ova linija će podići grešku ako status nije 2xx
            return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        raise HTTPException(status_code=exc.response.status_code, detail="Task worker service not available")

    
@app.get("/users/")
async def get_users():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{services['user_service']}/users/")
            response.raise_for_status()  # Ova linija će podići grešku ako status nije 2xx
            return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        raise HTTPException(status_code=exc.response.status_code, detail="User service not available")


@app.get("/health")
async def health_check():
    return {"status": "OK"}

# Funkcija za pokretanje svih servisa u zasebnim terminalima
def start_services():
    service_commands = [
        ["cmd.exe", "/c", "start", "cmd.exe", "/k", "uvicorn task_worker:app --host={} --port={}".format(task_worker_host, task_worker_port)],
        ["cmd.exe", "/c", "start", "cmd.exe", "/k", "uvicorn user_service:app --host={} --port={}".format(user_service_host, user_service_port)],
        ["cmd.exe", "/c", "start", "cmd.exe", "/k", "uvicorn notification_service:app --host={} --port={}".format(notification_service_host, notification_service_port)],
        ["cmd.exe", "/c", "start", "cmd.exe", "/k", "uvicorn health_check_service:app --host={} --port={}".format(health_check_service_host, health_check_service_port)],
        ["cmd.exe", "/c", "start", "cmd.exe", "/k", "uvicorn task_backup:app --host={} --port={}".format(task_backup_host, task_backup_port)]
    ]

    for command in service_commands:
        subprocess.Popen(command)


if __name__ == "__main__":
    import uvicorn
    # Pokretanje svih servisa prije pokretanja main aplikacije
    start_services()
    uvicorn.run(app, host=main_host, port=main_port)
