import asyncio
import websockets

async def listen():
    url = "ws://127.0.0.1:8003/ws/notifications"
    async with websockets.connect(url) as websocket:
        print("Connected to WebSocket server.")
        while True:
            message = await websocket.recv()
            print(f"Received notification: {message}")

asyncio.get_event_loop().run_until_complete(listen())
