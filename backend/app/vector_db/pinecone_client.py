from pinecone import Pinecone
from pinecone.exceptions import PineconeException
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.utils.logger import logger


class PineconeClient:

    def __init__(self, timeout_seconds: int = 30):
        self.index = None

        if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
            logger.warning("Pinecone not configured. RAG will be disabled.")
            return

        self._connect_with_retry()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _connect_with_retry(self):
        try:
            pc = Pinecone(api_key=settings.PINECONE_API_KEY, timeout=30)
            self.index = pc.Index(settings.PINECONE_INDEX_NAME)

            stats = self.index.describe_index_stats()
            logger.info(f"Connected to Pinecone ({stats.total_vector_count} vectors)")

        except PineconeException as e:
            logger.error(f"Pinecone connection failed: {e}")
            self.index = None  
            raise

    def is_healthy(self) -> bool:
        try:
            if not self.index:
                return False
            self.index.describe_index_stats()
            return True
        except Exception as e:
            logger.error(f"Pinecone health check failed: {e}")
            return False