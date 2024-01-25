import json
import logging
import sys
from contextlib import asynccontextmanager
from queue import Queue
from threading import Thread

import redis.asyncio as redis
from celery import Celery, shared_task
from celery.app.task import BaseTask
from fastapi import (
    FastAPI,
    Request,
    Response,
)
import uvicorn

from webhook.handler.viber import (
    viber_message_consumer,
    viber_validate_response
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

input_queue, output_queue = Queue(), Queue()

# Process viber events with high performance
viber_message_handler = Thread(target=viber_message_consumer, args=(input_queue, output_queue), daemon=True)
viber_message_handler.start()

# Validate viber response
viber_response_handler = Thread(target=viber_validate_response, args=(output_queue,), daemon=True)
viber_response_handler.start()

# Initialize the Redis client
redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

celery_app = Celery('main')
celery_app.config_from_object('celery_config')


@shared_task(
    bind=True,
    rate_limit="8/s",
    time_limit=120,  # 2 minutes
    soft_time_limit=60,  # 1 minute
    ignore_result=True,
)
def send_message_to_server(self: BaseTask, msg: dict):
    logger.info("Received message: %s", self.request.id)

    sender_id: str = msg.get("sender").get("id", "")
    message: dict = msg.get("message", {})
    logger.info("Received message: %s, from user: %s", message, sender_id)
    return


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # Terminate threads
    if not input_queue.empty():
        viber_message_handler.join(timeout=2)
    if not output_queue.empty():
        viber_response_handler.join(timeout=2)
    logger.info("Threads successfully terminated")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/viber/webhook")
async def viber_webhook(request: Request):
    data = await request.json()

    event = data.get("event")

    logger.debug("Received event: %s", event)

    if event == "conversation_started":
        user_id = data.get("user").get("id")
        input_queue.put(user_id)

    elif event == "message":
        sender_id: str = data.get("sender").get("id", "")
        message: dict = data.get("message", {})
        # we need to get hash sha256 from sender_id + message
        # if hash is in redis, then skip this event
        # else put sender_id + message to redis with ttl 5 mi

        hash_key = sender_id + json.dumps(message)
        cache_ttl: int = 300  # 5 minutes
        if not await redis_client.get(hash_key):
            await redis_client.setex(hash_key, cache_ttl, "1")
            logger.warning("Message for user %s does not exist", sender_id)
            send_message_to_server.s(data).apply_async()
        else:
            pass
            # For debug purposes
            # logger.warning("Message for user %s exists", sender_id)

    elif event == "webhook":
        # Response 200 OK, skip this event
        pass

    # Error handling
    else:
        logger.error("Unknown event")
        # Your regular processing for other events

    return Response(status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
