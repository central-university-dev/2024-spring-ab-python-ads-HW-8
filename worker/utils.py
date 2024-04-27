import json
import uuid
from typing import Any, Dict, Optional

import pika
import redis

redis_instance = redis.Redis(host="localhost", port=6379, db=0)


def publish_to_rabbitMQ(data: Dict[str, Any]) -> None:
    """Publishes data to RabbitMQ task queue.

    Args:
        data (Dict[str, Any]): The data to publish to the RabbitMQ.
    """
    credentials = pika.PlainCredentials("admin", "admin")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "localhost",
            5672,
            credentials=credentials,
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue="task_queue", durable=True)
    channel.basic_publish(exchange="", routing_key="task_queue", body=json.dumps(data))
    connection.close()


def create_request(input: Any) -> str:
    """Creates a new request in Redis and publishes it to RabbitMQ.

    Args:
        input (Any): The input data for the request.

    Returns:
        str: The unique ID of the created request.
    """
    random_id = str(uuid.uuid4())
    redis_instance.set(
        random_id, json.dumps({"input": input, "status": "processing", "output": ""})
    )
    publish_to_rabbitMQ({"request_id": random_id, "input": input})
    return random_id


def get_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a request's data from Redis based on its ID.

    Args:
        request_id (str): The ID of the request to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The data of the request if found, otherwise None.
    """
    request_data = redis_instance.get(request_id)
    if request_data:
        return json.loads(request_data)
    return None


def update_request(request_id: str, status: str, output: Any) -> None:
    """Updates a request's status and output in Redis.

    Args:
        request_id (str): The ID of the request to update.
        status (str): The new status of the request.
        output (Any): The output data to be stored with the request.
    """
    request_details = get_request(request_id)
    redis_instance.set(
        request_id,
        json.dumps(
            {"input": request_details["input"], "status": status, "output": output}
        ),
    )
