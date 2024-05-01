import aio_pika
import aioredis
import asyncio
import json
from sklearn.model_selection import train_test_split
from sklift.models import SoloModel, TwoModels
from sklift.metrics import qini_auc_score
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

def get_data() -> pd.DataFrame:
    """
    Load data from a CSV file.
    """
    data = pd.read_csv('data.csv')
    return data

def get_classifier(classifier_name: str) -> object:
    """
    Get a classifier based on the provided name.
    """
    if classifier_name == "CatBoostClassifier":
        return CatBoostClassifier(verbose=0, thread_count=2)
    elif classifier_name == "RandomForestClassifier":
        return RandomForestClassifier()

async def train_and_evaluate(request_data: dict) -> dict:
    """
    Train a model based on the provided data and approach, and evaluate it.
    """
    data = get_data()

    X_train, X_test, y_train, y_test = train_test_split(data.drop(['target'], axis=1), data['target'], test_size=0.2)

    classifier = get_classifier(request_data["classifier"])

    model = None
    if request_data["approach"] == "solo-model":
        model = SoloModel(estimator=classifier)
    elif request_data["approach"] == "two-model":
        model = TwoModels(estimator_trmnt=classifier, estimator_ctrl=classifier, method='vanilla')

    if model:
        model.fit(X_train, y_train, treatment=X_train['treatment'])
        predictions = model.predict(X_test)
        score = qini_auc_score(y_test, predictions, X_test['treatment'])
        return {"status": "completed", "score": score}
    else:
        return {"status": "error", "message": "Invalid modeling approach"}

async def process_message(message: aio_pika.IncomingMessage) -> None:
    """
    Process a message from the queue.
    """
    async with message.process():
        request_data = json.loads(message.body)
        print("Обработка:", request_data)

        model_result = await train_and_evaluate(request_data)

        redis = await aioredis.from_url("redis://localhost:6379", decode_responses=True)
        await redis.set(request_data['request_id'], json.dumps(model_result))

async def main() -> None:
    """
    Main function to run the worker.
    """
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    queue_name = "model_queue"
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.consume(process_message)
        print("Worker запущен. Ожидание задач...")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
