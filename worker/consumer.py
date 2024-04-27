import json

import pika
from pika import Channel, BasicDeliver, BasicProperties

from model import UpliftPipeline
from utils import update_request


def callback(ch: Channel, method: BasicDeliver, properties: BasicProperties, body: bytes) -> None:
    """
    Callback function to handle RabbitMQ messages.

    :param ch: Channel instance through which the message was received.
    :param method: Delivery method providing delivery data.
    :param properties: Message properties.
    :param body: The message body.
    """
    body = json.loads(body)
    request_id = body["request_id"]
    print(f"Received request with ID: {request_id}")
    train_model = UpliftPipeline()
    output = train_model.train_and_evaluate_model(
        body["approach"], body["classifier"], body["train_size"]
    )
    update_request(request_id, "done", output)


def start_consumer():
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
    channel.basic_consume(
        queue="task_queue", on_message_callback=callback, auto_ack=True
    )
    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
