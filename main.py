import asyncio
import os
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import redis
import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from flash_sale import buy_ticket
from redis_config import CHANNEL, REDIS_URL, STOCK, client


@asynccontextmanager
async def lifespan(app):
    initial_stock = int(os.getenv("INITIAL_STOCK", "10"))
    if initial_stock < 0:
        raise ValueError("INITIAL_STOCK must be nonnegative")
    async with aioredis.Redis.from_url(
        REDIS_URL, decode_responses=True, socket_connect_timeout=3
    ) as connection:
        await connection.set(STOCK, initial_stock, nx=True)
        app.state.redis = connection
        yield


app = FastAPI(title="Redis 秒殺搶購系統 API", lifespan=lifespan)


class BuyRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"))


@app.get("/healthz")
def health():
    try:
        client.ping()
    except redis.RedisError:
        raise HTTPException(503, "Redis unavailable")
    return {"status": "ok"}


@app.get("/api/stock")
def get_stock():
    return {"stock": int(client.get(STOCK) or 0)}


@app.post("/api/buy")
def buy_ticket_api(req: BuyRequest):
    outcome = buy_ticket(req.user_id)
    if outcome == "sold_out":
        raise HTTPException(400, "票已售完！")
    if outcome == "duplicate":
        raise HTTPException(400, "您已經買過了，不可重複購票！")
    if outcome == "busy":
        raise HTTPException(503, "系統繁忙，請重試！")
    return {"message": "搶購成功！", "user_id": req.user_id}


async def push_stock(websocket, connection):
    async with connection.pubsub() as pubsub:
        await pubsub.subscribe(CHANNEL)
        async for message in pubsub.listen():
            if message["type"] in ("subscribe", "message"):
                current = await connection.get(STOCK)
                await websocket.send_text(current or "0")


@app.websocket("/ws/stock")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    publisher = asyncio.create_task(push_stock(websocket, websocket.app.state.redis))
    try:
        while True:
            receiver = asyncio.create_task(websocket.receive())
            try:
                done, _ = await asyncio.wait(
                    (publisher, receiver), return_when=asyncio.FIRST_COMPLETED
                )
                if publisher in done:
                    publisher.result()
                    return
                if receiver.result()["type"] == "websocket.disconnect":
                    return
            finally:
                receiver.cancel()
                await asyncio.gather(receiver, return_exceptions=True)
    except (WebSocketDisconnect, OSError):
        pass
    except redis.RedisError:
        with suppress(WebSocketDisconnect, OSError):
            await websocket.close(code=1013)
    finally:
        publisher.cancel()
        await asyncio.gather(publisher, return_exceptions=True)
