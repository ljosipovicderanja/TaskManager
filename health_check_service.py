from fastapi import FastAPI, HTTPException, BackgroundTasks
from typing import Dict
import httpx
import asyncio
import logging
from database import logs_collection
from datetime import datetime

# Postavljanje logiranja
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Definicija servisa koje ćemo pratiti
services = {
    "task_manager": "http://127.0.0.1:8001/health",
    "user_service": "http://127.0.0.1:8002/health",
    "notification_service": "http://127.0.0.1:8003/health"
}

# Globalna varijabla za spremanje statusa servisa
service_status = {service: "UNKNOWN" for service in services}

# Funkcija za dodavanje logova u MongoDB
async def log_event(message: str, level: str = "INFO"):
    log_document = {
        "message": message,
        "level": level,
        "timestamp": datetime.utcnow(),
    }
    await logs_collection.insert_one(log_document)

# Funkcija za provjeru statusa pojedinačnog servisa
async def check_service(service_name: str, service_url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(service_url)
            response.raise_for_status()
            service_status[service_name] = "UP"
            await log_event(f"Service {service_name} is UP.")
    except httpx.RequestError as exc:
        service_status[service_name] = "DOWN"
        await log_event(f"Service {service_name} is DOWN. Error: {exc}", "ERROR")
    except httpx.HTTPStatusError as exc:
        service_status[service_name] = "DOWN"
        await log_event(f"Service {service_name} returned status {exc.response.status_code}. Marking as DOWN.", "ERROR")

# Funkcija koja se izvršava u pozadini
async def periodic_health_check():
    while True:
        logger.info("Starting periodic health check...")
        for service_name, service_url in services.items():
            await check_service(service_name, service_url)
        await asyncio.sleep(10)  # Čekanje između provjera (10 sekundi)
        logger.info("Periodic health check completed.")

# Ruta za ručnu provjeru statusa servisa
@app.get("/health/{service_name}")
async def health_check(service_name: str) -> Dict[str, str]:
    if service_name not in services:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"service": service_name, "status": service_status.get(service_name, "UNKNOWN")}

# Ruta za provjeru statusa svih servisa
@app.get("/health/")
async def health_check_all() -> Dict[str, Dict[str, str]]:
    return service_status

# Pokretanje background taska prilikom pokretanja aplikacije
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_health_check())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
