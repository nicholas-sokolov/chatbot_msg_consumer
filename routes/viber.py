import json
import logging

from fastapi import (
    Request,
    Response, APIRouter,
)

from redis_client.client import redis_client
from celery_worker import send_message_to_server
from webhook_handler.viber import viber_input_queue

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/viber/webhook")
async def viber_webhook(request: Request):
    try:
        data = await request.json()

        event = data.get("event")

        logger.debug("Received event: %s", event)

        if event == "conversation_started":
            user_id = data.get("user").get("id")
            viber_input_queue.put(user_id)

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
            logger.error("Unknown event %s", data)
            # Your regular processing for other events

    except Exception as e:
        logger.exception(e)

    return Response(status_code=200)
