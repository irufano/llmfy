import json
from typing import Optional

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.flow_engine.checkpointer.base_checkpointer import (
    BaseCheckpointer,
    Checkpoint,
)

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisCheckpointer(BaseCheckpointer):
    """Redis checkpoint storage backend."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "llmfy_checkpoint:",
        ttl: Optional[int] = None,
    ):
        """
        Initialize the Redis checkpointer.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for checkpoints
            ttl: Time-to-live in seconds for checkpoints (None = no expiration)
        """
        if not REDIS_AVAILABLE:
            raise LLMfyException(
                "redis package is not installed. redis package is required for RedisCheckpointer. "
                'Install it using `pip install "llmfy[redis]"`'
            )

        self.redis_url = redis_url
        self.prefix = prefix
        self.ttl = ttl
        self._client: Optional[redis.Redis] = None

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._client

    def _session_key(self, session_id: str) -> str:
        """Get Redis key for session's checkpoint list."""
        return f"{self.prefix}session:{session_id}"

    def _checkpoint_key(self, checkpoint_id: str) -> str:
        """Get Redis key for specific checkpoint."""
        return f"{self.prefix}checkpoint:{checkpoint_id}"

    async def save(self, checkpoint: Checkpoint) -> None:
        """
        Save a checkpoint to Redis.

        Args:
            checkpoint: The checkpoint to save
        """
        client = await self._get_client()

        session_id = checkpoint.metadata.session_id
        checkpoint_id = checkpoint.metadata.checkpoint_id
        timestamp = checkpoint.metadata.timestamp.timestamp()

        # Save checkpoint data
        checkpoint_key = self._checkpoint_key(checkpoint_id)
        checkpoint_data = json.dumps(checkpoint.to_dict())

        await client.set(checkpoint_key, checkpoint_data)

        if self.ttl:
            await client.expire(checkpoint_key, self.ttl)

        # Add to thread's sorted set (sorted by timestamp)
        session_key = self._session_key(session_id)
        await client.zadd(session_key, {checkpoint_id: timestamp})

        if self.ttl:
            await client.expire(session_key, self.ttl)

    async def load(
        self,
        session_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Checkpoint]:
        """
        Load a checkpoint from Redis.

        Args:
            session_id: The session ID
            checkpoint_id: Specific checkpoint ID, or None for latest

        Returns:
            The checkpoint if found, None otherwise
        """
        client = await self._get_client()

        if checkpoint_id is None:
            # Get latest checkpoint ID from sorted set
            session_key = self._session_key(session_id)
            results = await client.zrevrange(session_key, 0, 0)

            if not results:
                return None

            checkpoint_id = results[0]

        # Load checkpoint data
        checkpoint_key = self._checkpoint_key(checkpoint_id)  # type: ignore
        data = await client.get(checkpoint_key)

        if data is None:
            return None

        checkpoint_dict = json.loads(data)
        return Checkpoint.from_dict(checkpoint_dict)

    async def list(self, session_id: str, limit: int = 10) -> list[Checkpoint]:
        """
        List checkpoints for a thread.

        Args:
            session_id: The session ID
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoints, newest first
        """
        client = await self._get_client()

        # Get checkpoint IDs from sorted set (newest first)
        thread_key = self._session_key(session_id)
        checkpoint_ids = await client.zrevrange(thread_key, 0, limit - 1)

        if not checkpoint_ids:
            return []

        # Load all checkpoints
        checkpoints = []
        for checkpoint_id in checkpoint_ids:
            checkpoint = await self.load(session_id, checkpoint_id)
            if checkpoint:
                checkpoints.append(checkpoint)

        return checkpoints

    async def delete(self, session_id: str, checkpoint_id: Optional[str] = None) -> None:
        """
        Delete checkpoint(s) from Redis.

        Args:
            session_id: The session ID
            checkpoint_id: Specific checkpoint ID, or None to delete all for thread
        """
        client = await self._get_client()
        session_key = self._session_key(session_id)

        if checkpoint_id:
            # Delete specific checkpoint
            checkpoint_key = self._checkpoint_key(checkpoint_id)
            await client.delete(checkpoint_key)
            await client.zrem(session_key, checkpoint_id)
        else:
            # Delete all checkpoints for thread
            checkpoint_ids = await client.zrange(session_key, 0, -1)

            if checkpoint_ids:
                # Delete all checkpoint data
                checkpoint_keys = [self._checkpoint_key(cid) for cid in checkpoint_ids]
                await client.delete(*checkpoint_keys)

            # Delete session sorted set
            await client.delete(session_key)

    async def clear_all(self) -> None:
        """Clear all checkpoints from Redis."""
        client = await self._get_client()

        # Find all keys with our prefix
        pattern = f"{self.prefix}*"
        cursor = 0

        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)

            if keys:
                await client.delete(*keys)

            if cursor == 0:
                break

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
