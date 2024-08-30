from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict, Any
import httpx
import asyncio
import logging
from database import logs_collection  # Uvjerite se da je pravilno postavljen
from datetime import datetime, timezone
import json

with open("config.json") as config_file:
    config = json.load(config_file)

# Postavljanje logiranja
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Konfiguracija
health_check_service_host = config["health_check_service_host"]
health_check_service_port = config["health_check_service_port"]

# Definicija servisa koje ćemo pratiti
services = {
    "main": "http://127.0.0.1:8000/health",
    "task_worker": "http://127.0.0.1:8001/health",
    "user_service": "http://127.0.0.1:8002/health",
    "notification_service": "http://127.0.0.1:8003/health",
    "task_backup": "http://127.0.0.1:8005/health"
}

# Globalna varijabla za spremanje statusa servisa
service_status = {service: "UNKNOWN" for service in services}

# Funkcija za dodavanje logova u MongoDB
async def log_event(message: str, level: str = "INFO"):
    log_document = {
        "message": message,
        "level": level,
        "timestamp": datetime.now(timezone.utc),  # Pravilno korištenje timezone-aware datetimea
    }
    await logs_collection.insert_one(log_document)

# Funkcija za provjeru statusa pojedinačnog servisa
async def check_service(service_name: str, service_url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(service_url)
            response.raise_for_status()
            service_status[service_name] = {"status": "UP"}
            await log_event(f"Service {service_name} is UP.")
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        service_status[service_name] = {"status": "DOWN"}
        await log_event(f"Service {service_name} is DOWN. Error: {exc}", "ERROR")
        logger.error(f"Service {service_name} is DOWN. Error: {exc}")
    except Exception as exc:
        service_status[service_name] = {"status": "ERROR", "details": str(exc)}
        await log_event(f"Service {service_name} encountered an unexpected error: {exc}", "ERROR")
        logger.error(f"Unexpected error for service {service_name}: {exc}")

# Funkcija koja se izvršava u pozadini
async def periodic_health_check():
    while True:
        logger.info("Starting periodic health check...")
        tasks = [check_service(service_name, service_url) for service_name, service_url in services.items()]
        await asyncio.gather(*tasks)
        logger.info("Periodic health check completed.")
        await asyncio.sleep(10)  # Čekanje između provjera (10 sekundi)

# Ruta za ručnu provjeru statusa servisa
@app.get("/health/{service_name}")
async def health_check(service_name: str) -> Dict[str, Any]:
    if service_name not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"service": service_name, "status": service_status.get(service_name, {"status": "UNKNOWN"})}

# Ruta za provjeru statusa svih servisa
@app.get("/health")
async def health_check_all() -> Dict[str, Dict[str, str]]:
    return service_status

# Pokretanje background taska prilikom pokretanja aplikacije
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_health_check())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=health_check_service_host, port=health_check_service_port)
