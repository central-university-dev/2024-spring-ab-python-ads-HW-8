from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
import aioredis
import aio_pika
import json

app = FastAPI()

redis: aioredis.Redis = aioredis.from_url("redis://localhost:6379", encoding="utf-8", decode_responses=True)

class ScoreRequest(BaseModel):
    approach: str
    classifier: str
    train_size: float

async def send_to_rabbitmq(request_id: str, data: str) -> None:
    """
    Send data to RabbitMQ.
    """
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=data.encode()),
            routing_key="model_queue",
        )

@app.on_event("startup")
async def startup_event() -> None:
    """
    Connect to Redis on startup.
    """
    app.state.redis = await aioredis.from_url("redis://localhost:6379", decode_responses=True)

@app.post("/score")
async def score(request: ScoreRequest) -> dict:
    """
    Handle a POST request to the "/score" endpoint.
    """
    request_id = str(uuid.uuid4())
    request_data = request.json()
    await app.state.redis.set(request_id, json.dumps({"status": "pending"}))
    await send_to_rabbitmq(request_id, json.dumps(request_data))
    return {"request_id": request_id}

@app.get("/score/result/{request_id}")
async def score_result(request_id: str) -> dict:
    """
    Handle a GET request to the "/score/result/{request_id}" endpoint.
    """
    result = await app.state.redis.get(request_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return {"result": json.loads(result)}
