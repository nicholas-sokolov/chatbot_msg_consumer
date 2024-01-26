import logging
import time
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty

logger = logging.getLogger(__name__)

# Static response for conversation_started event
conversation_started_response = {
    "min_api_version": 8,
    "type": "text",
    "text": "Добро пожаловать! Это сообщение по-умолчанию, обратитесь к менеджерам, чтоб его изменить.",
    "sender": {
        "name": "Автоматический ответ",
        "avatar": None
    }
}


def send_broadcast(user_id_list: list[str]):
    # For debug purposes, how many users we send message
    logger.warning("Send broadcast message to %d users", len(user_id_list))

    # Viber has API to send broadcast message to list of users, let's mock it with sleep 500ms
    time.sleep(0.5)
    return conversation_started_response


def viber_message_consumer(in_queue: Queue, out_queue: Queue):
    """Handle Viber events with high performance

    Put user_id to in_queue and after combine them to list of users and send broadcast message
    Use ThreadPoolExecutor to send broadcast message in parallel

    Put Future to out_queue and validate response in another thread

    :param in_queue: Queue with user_id
    :param out_queue: Queue with Future
    :return: None
    """
    executor = ThreadPoolExecutor()

    user_id_list: list[str] = []
    last_sent_time: float = time.time()

    def _send_message(recipients: list[str]) -> tuple[float, list[str]]:
        future = executor.submit(send_broadcast, recipients)
        out_queue.put(future)
        return time.time(), []

    # Viber has limit 300 users per broadcast message
    max_recipients = 300

    # Viber has limit 500 messages for 10 minutes (600 seconds)
    rate_limit = 500
    time_period = 600  # seconds
    delay_between_requests = time_period / rate_limit

    while True:
        try:
            user_id = in_queue.get(block=False)
        except Empty:
            if len(user_id_list):
                # Send message to users while queue is empty and wait next message
                last_sent_time, user_id_list = _send_message(user_id_list)

            time.sleep(0.5)
            continue

        if user_id is None:
            # queue is closed
            if len(user_id_list):
                _send_message(user_id_list)

            # break loop and exit thread with executor.shutdown()
            break

        user_id_list.append(user_id)

        if any([
            len(user_id_list) == max_recipients,
            time.time() - last_sent_time > delay_between_requests,
        ]):
            last_sent_time, user_id_list = _send_message(user_id_list)

        in_queue.task_done()


def viber_validate_response(in_queue: Queue):
    """Validate response from Viber API

    When we send broadcast message to list of users, we get Future object.
    This thread get Future from queue and validate response.

    :param in_queue: Queue with Future
    :return: None
    """
    while True:
        try:
            future: Future | None = in_queue.get(block=False)
        except Empty:
            time.sleep(0.5)
            continue

        if future is None:
            # queue is closed
            break

        mock_result = True
        try:
            result = future.result(timeout=5)
        except Exception as e:
            logger.error("Error: %s", e)
        else:
            if not mock_result:
                logger.error("Invalid response: %s", result)

        in_queue.task_done()
