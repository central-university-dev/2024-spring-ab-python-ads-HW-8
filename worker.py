import pika
import json
import redis
from sklift.models import SoloModel, TwoModels
from sklift.datasets import fetch_x5
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

redis_client = redis.Redis(host="redis-service", port=6379, db=0)
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq-service"))
channel = connection.channel()


def train_model(ch, method, properties, body):
    data = json.loads(body)
    request_id = data["request_id"]
    train_size = float(data["train_size"])
    approach = data["approach"]
    classifier = data["classifier"]

    x5_data = fetch_x5()
    X = x5_data.data
    y = x5_data.target
    treatment = x5_data.treatment
    X_train, X_test, y_train, y_test, treat_train, treat_test = train_test_split(
        X, y, treatment, test_size=1 - train_size
    )

    if classifier == "catboost":
        estimator = CatBoostClassifier(verbose=0, iterations=10)
    elif classifier == "random-forest":
        estimator = RandomForestClassifier()

    if approach == "solo-model":
        model = SoloModel(estimator)
    elif approach == "two-model":
        model = TwoModels(estimator_treatment=estimator, estimator_control=estimator)

    model.fit(X_train, y_train, treat_train)
    score = model.score(X_test, y_test, treat_test)

    redis_client.set(request_id, f"Completed with score: {score}")


channel.basic_consume(
    queue="training_queue", on_message_callback=train_model, auto_ack=True
)
channel.start_consuming()
