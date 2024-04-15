from flask import Flask, request, jsonify
import uuid
import redis
import pika
import json

app = Flask(__name__)
redis_client = redis.Redis(host="redis-service", port=6379, db=0)
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq-service"))
channel = connection.channel()

channel.queue_declare(queue="training_queue")


@app.route("/score", methods=["POST"])
def score():
    data = request.json
    approach = data.get("approach")
    classifier = data.get("classifier")
    train_size = data.get("train_size")

    request_id = str(uuid.uuid4())
    redis_client.set(request_id, "processing")

    task_data = {
        "approach": approach,
        "classifier": classifier,
        "train_size": train_size,
        "request_id": request_id,
    }
    channel.basic_publish(
        exchange="", routing_key="training_queue", body=json.dumps(task_data)
    )

    return jsonify({"request_id": request_id})


@app.route("/score/result", methods=["GET"])
def score_result():
    request_id = request.args.get("request_id")
    result = redis_client.get(request_id)
    if result is None:
        return jsonify({"status": "not found"}), 404
    return jsonify({"status": result.decode()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
