from fastapi import FastAPI, HTTPException
from typing import Dict
import httpx

app = FastAPI()

# Definicija servisa koje ćemo pratiti
services = {
    "task_manager": "http://127.0.0.1:8001/health",
    "user_service": "http://127.0.0.1:8002/health",
    "notification_service": "http://127.0.0.1:8003/health"
}

@app.get("/health/{service_name}")
async def health_check(service_name: str) -> Dict[str, str]:
    if service_name not in services:
        raise HTTPException(status_code=404, detail="Service not found")

    service_url = services[service_name]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(service_url)
            response.raise_for_status()
    except httpx.RequestError as exc:
        return {"service": service_name, "status": "DOWN", "detail": str(exc)}
    except httpx.HTTPStatusError as exc:
        return {"service": service_name, "status": "DOWN", "detail": f"Error response {exc.response.status_code} from {service_url}"}

    return {"service": service_name, "status": "UP"}

@app.get("/health/")
async def health_check_all() -> Dict[str, Dict[str, str]]:
    results = {}
    for service_name, service_url in services.items():
        results[service_name] = await health_check(service_name)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
