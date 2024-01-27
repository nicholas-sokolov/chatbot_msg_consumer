import os
from celery.app.task import Task
import logging

from celery import Celery
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')

celery_app = Celery(
    'celery_worker',
    broker=f'redis://{redis_host}:{redis_port}/0',
    backend=f'redis://{redis_host}:{redis_port}/0',
)


@celery_app.task(
    bind=True,
    rate_limit="8/s",
    time_limit=120,  # 2 minutes
    soft_time_limit=60,  # 1 minute
    ignore_result=True,
)
def send_message_to_server(self: Task, msg: dict):
    logger.info("Received message: %s", self.request.id)

    sender_id: str = msg.get("sender").get("id", "")
    message: dict = msg.get("message", {})
    logger.info("Received message: %s, from user: %s", message, sender_id)
    return
