import logging
import sys
from contextlib import asynccontextmanager
from queue import Queue
from threading import Thread

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
        # Handle message events
        pass

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
