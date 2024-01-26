import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

from routes import viber
from webhook_handler.viber import (
    viber_input_queue,
    viber_message_handler,
    viber_output_queue,
    viber_response_handler,
)

logger = logging.getLogger(__name__)

load_dotenv()  # take environment variables from .env.


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # Terminate threads
    if not viber_input_queue.empty():
        viber_message_handler.join(timeout=2)
    if not viber_output_queue.empty():
        viber_response_handler.join(timeout=2)
    logger.info("Threads successfully terminated")


app = FastAPI(lifespan=lifespan)

app.include_router(viber.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
