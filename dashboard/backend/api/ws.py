"""WebSocket endpoint for real-time project updates via Redis pub/sub."""
import asyncio
import json
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis as sync_redis

router = APIRouter()
CHANNEL_PREFIX = "ut:project:"


@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": f"Connected to {project_id}"
    }))

    r = sync_redis.Redis(host="localhost", port=6379, db=0)
    pubsub = r.pubsub()
    pubsub.subscribe(f"{CHANNEL_PREFIX}{project_id}")

    stop_event = threading.Event()

    def redis_listener():
        for message in pubsub.listen():
            if stop_event.is_set():
                break
            if message["type"] == "message":
                asyncio.run_coroutine_threadsafe(
                    websocket.send_text(message["data"].decode("utf-8")),
                    asyncio.get_event_loop(),
                )

    thread = threading.Thread(target=redis_listener, daemon=True)
    thread.start()

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        stop_event.set()
        pubsub.close()
