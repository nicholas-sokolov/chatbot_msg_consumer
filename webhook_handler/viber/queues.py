from queue import Queue
from threading import Thread
from .handler import viber_message_consumer, viber_validate_response

input_queue, output_queue = Queue(), Queue()

# Process viber events with high performance
viber_message_handler = Thread(target=viber_message_consumer, args=(input_queue, output_queue), daemon=True)
viber_message_handler.start()

# Validate viber response
viber_response_handler = Thread(target=viber_validate_response, args=(output_queue,), daemon=True)
viber_response_handler.start()
