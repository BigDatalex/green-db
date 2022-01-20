from logging import getLogger

from redis import Redis
from rq import Queue, Retry

from core import log
from core.constants import (
    WORKER_FUNCTION_EXTRACT,
    WORKER_FUNCTION_SCRAPING,
    WORKER_QUEUE_EXTRACT,
    WORKER_QUEUE_SCRAPING,
)
from core.domain import ScrapedPage
from core.redis import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, REDIS_USER

log.setup_logger(__name__)
logger = getLogger(__name__)


class MessageQueue:
    def __init__(self) -> None:
        self.__redis_connection = Redis(
            host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, username=REDIS_USER
        )

        self.__scraping_queue = Queue(WORKER_QUEUE_SCRAPING, connection=self.__redis_connection)
        self.__extract_queue = Queue(WORKER_QUEUE_EXTRACT, connection=self.__redis_connection)

        logger.info("Redis connection established and message queues initialized.")

    def add_scraping(self, table_name: str, scraped_page: ScrapedPage) -> None:
        self.__scraping_queue.enqueue(
            WORKER_FUNCTION_SCRAPING,
            args=(table_name, scraped_page),
            job_timeout=10,
            result_ttl=1,
            retry=Retry(max=5, interval=30),
        )

    def add_extract(self, table_name: str, row_id: int) -> None:
        self.__extract_queue.enqueue(
            WORKER_FUNCTION_EXTRACT,
            args=(table_name, row_id),
            job_timeout=10,
            result_ttl=1,
            retry=Retry(max=5, interval=30),
        )
