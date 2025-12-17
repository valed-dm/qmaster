import time

from celery import shared_task
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


@shared_task(name="process_order")
def process_order(order_id: str) -> str:
    """
    Simulates background order processing.
    Triggered by RabbitMQ consumers.
    """
    logger.info(f"Received order {order_id} for processing...")

    time.sleep(2)

    msg = f"Order {order_id} processed"
    print(msg)
    logger.info(msg)

    return msg
