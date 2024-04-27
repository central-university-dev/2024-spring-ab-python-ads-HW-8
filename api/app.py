from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils import (create_request, get_redis_connection, get_request,
                   publish_to_rabbitMQ)

app = FastAPI()


class Task(BaseModel):
    approach: str
    classifier: str
    train_size: float


@app.post("/score/")
async def create_score(task: Task):
    task_data = task.dict()
    task_id = create_request(task_data)
    return {"task_id": task_id}


@app.get("/score/result/{task_id}")
async def get_result(task_id: str):
    result = get_request(task_id)
    if result is None:
        return {"error": "Task not found"}
    return result
