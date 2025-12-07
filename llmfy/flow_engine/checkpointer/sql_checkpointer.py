import asyncio
from typing import List, Optional

from sqlalchemy import TypeDecorator
from sqlalchemy.dialects import mysql, postgresql

from llmfy.exception.llmfy_exception import LLMfyException
from llmfy.flow_engine.checkpointer.base_checkpointer import (
    BaseCheckpointer,
    Checkpoint,
    CheckpointMetadata,
)

try:
    from sqlalchemy import (
        Column,
        DateTime,
        Index,
        Integer,
        String,
        Text,
        create_engine,
        delete,
        select,
    )
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.orm import declarative_base, sessionmaker

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class TimestampMilliseconds(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(mysql.DATETIME(fsp=3))
        elif dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.TIMESTAMP(precision=3))
        else:
            return dialect.type_descriptor(DateTime())


class LongText(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.TEXT())
        elif dialect.name == "mysql":
            return dialect.type_descriptor(mysql.LONGTEXT())
        else:
            return dialect.type_descriptor(Text())


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class CheckpointModel(Base):
        """SQLAlchemy model for checkpoint storage."""

        __tablename__ = "llmfy_checkpoint"

        checkpoint_id = Column(String(255), primary_key=True)
        thread_id = Column(String(255), nullable=False, index=True)
        timestamp = Column(TimestampMilliseconds, nullable=False)
        node_name = Column(String(255), nullable=False)
        step = Column(Integer, nullable=False)
        state = Column(LongText, nullable=False)

        # Composite index for efficient queries
        __table_args__ = (Index("idx_thread_timestamp", "thread_id", "timestamp"),)

else:
    raise LLMfyException(
        "SQLAlchemy package is not installed. SQLAlchemy package is required for SQLCheckpointer. "
        'Install it using `pip install "llmfy[SQLAlchemy]"`'
    )


class SQLCheckpointer(BaseCheckpointer):
    """
    SQL database checkpoint storage backend using SQLAlchemy.

    Supports both sync and async drivers for multiple databases:
    - PostgreSQL (async: asyncpg, sync: psycopg2)
    - MySQL (async: aiomysql, sync: pymysql)
    - SQLite (async: aiosqlite, sync: built-in)
    """

    def __init__(self, connection_string: str, echo: bool = False):
        """
        Initialize the SQL database checkpointer.

        Args:
            connection_string: SQLAlchemy connection string (sync or async)
            echo: Whether to echo SQL statements (for debugging)

        Example connection strings:

            ASYNC (Recommended):
            - PostgreSQL: "postgresql+asyncpg://user:password@localhost:5432/dbname"
            - MySQL:      "mysql+aiomysql://user:password@localhost:3306/dbname"
            - SQLite:     "sqlite+aiosqlite:///./database.db"

            SYNC (For compatibility with pymysql, psycopg2, etc):
            - PostgreSQL: "postgresql+psycopg2://user:password@localhost:5432/dbname"
            - MySQL:      "mysql+pymysql://user:password@localhost:3306/dbname"
            - SQLite:     "sqlite:///./database.db"

        Installation:
            Async drivers (recommended):
            - pip install sqlalchemy asyncpg --break-system-packages      # PostgreSQL
            - pip install sqlalchemy aiomysql --break-system-packages     # MySQL
            - pip install sqlalchemy aiosqlite --break-system-packages    # SQLite

            Sync drivers (for compatibility):
            - pip install sqlalchemy psycopg2-binary --break-system-packages  # PostgreSQL
            - pip install sqlalchemy pymysql --break-system-packages          # MySQL
            - pip install sqlalchemy --break-system-packages                  # SQLite (built-in)
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy is required for SQLCheckpointer.\n"
                "Install with: pip install sqlalchemy --break-system-packages\n\n"
                "Then install your database driver:\n"
                "  Async (recommended):\n"
                "    pip install asyncpg --break-system-packages      # PostgreSQL\n"
                "    pip install aiomysql --break-system-packages     # MySQL\n"
                "    pip install aiosqlite --break-system-packages    # SQLite\n\n"
                "  Sync (for compatibility):\n"
                "    pip install psycopg2-binary --break-system-packages  # PostgreSQL\n"
                "    pip install pymysql --break-system-packages          # MySQL\n"
                "    (SQLite is built-in, no extra package needed)"
            )

        self.connection_string = connection_string

        # Detect if using async or sync driver
        self.is_async = any(
            driver in connection_string.lower()
            for driver in ["asyncpg", "aiomysql", "aiosqlite", "+async"]
        )

        if self.is_async:
            # Async mode
            self.engine = create_async_engine(connection_string, echo=echo)
            self.session_maker = async_sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        else:
            # Sync mode
            self.engine = create_engine(connection_string, echo=echo)
            self.session_maker = sessionmaker(bind=self.engine)

        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database tables are created."""
        if not self._initialized:
            if self.is_async:
                async with self.engine.begin() as conn:  # type: ignore
                    await conn.run_sync(Base.metadata.create_all)
            else:
                # Sync initialization - run in executor to keep it async
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, Base.metadata.create_all, self.engine)

            self._initialized = True

    async def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to SQL database."""
        await self._ensure_initialized()

        model = CheckpointModel(
            checkpoint_id=checkpoint.metadata.checkpoint_id,
            thread_id=checkpoint.metadata.thread_id,
            timestamp=checkpoint.metadata.timestamp,
            node_name=checkpoint.metadata.node_name,
            step=checkpoint.metadata.step,
            state=Checkpoint._serialize_state(checkpoint.state),
        )

        if self.is_async:
            async with self.session_maker() as session:  # type: ignore
                session.add(model)
                await session.commit()
        else:
            # Sync operation - run in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._save_sync, model)

    def _save_sync(self, model: CheckpointModel):
        """Helper for sync save."""
        with self.session_maker() as session:  # type: ignore
            session.add(model)
            session.commit()

    async def load(
        self,
        thread_id: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[Checkpoint]:
        """Load a checkpoint from SQL database."""
        await self._ensure_initialized()

        if self.is_async:
            return await self._load_async(thread_id, checkpoint_id)
        else:
            # Sync operation - run in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._load_sync, thread_id, checkpoint_id
            )

    async def _load_async(
        self, thread_id: str, checkpoint_id: Optional[str]
    ) -> Optional[Checkpoint]:
        """Helper for async load."""
        async with self.session_maker() as session:  # type: ignore
            if checkpoint_id:
                stmt = select(CheckpointModel).where(
                    CheckpointModel.checkpoint_id == checkpoint_id,
                    CheckpointModel.thread_id == thread_id,
                )
            else:
                stmt = (
                    select(CheckpointModel)
                    .where(CheckpointModel.thread_id == thread_id)
                    .order_by(CheckpointModel.timestamp.desc())
                    .limit(1)
                )

            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            return self._model_to_checkpoint(model) if model else None

    def _load_sync(
        self,
        thread_id: str,
        checkpoint_id: Optional[str],
    ) -> Optional[Checkpoint]:
        """Helper for sync load."""
        with self.session_maker() as session:  # type: ignore
            if checkpoint_id:
                stmt = select(CheckpointModel).where(
                    CheckpointModel.checkpoint_id == checkpoint_id,
                    CheckpointModel.thread_id == thread_id,
                )
            else:
                stmt = (
                    select(CheckpointModel)
                    .where(CheckpointModel.thread_id == thread_id)
                    .order_by(CheckpointModel.timestamp.desc())
                    .limit(1)
                )

            result = session.execute(stmt)
            model = result.scalar_one_or_none()

            return self._model_to_checkpoint(model) if model else None

    async def list(self, thread_id: str, limit: int = 10) -> List[Checkpoint]:
        """List checkpoints for a thread."""
        await self._ensure_initialized()

        if self.is_async:
            return await self._list_async(thread_id, limit)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._list_sync, thread_id, limit)

    async def _list_async(self, thread_id: str, limit: int) -> List[Checkpoint]:
        """Helper for async list."""
        async with self.session_maker() as session:  # type: ignore
            stmt = (
                select(CheckpointModel)
                .where(CheckpointModel.thread_id == thread_id)
                .order_by(CheckpointModel.timestamp.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_checkpoint(model) for model in models]

    def _list_sync(self, thread_id: str, limit: int) -> List[Checkpoint]:
        """Helper for sync list."""
        with self.session_maker() as session:  # type: ignore
            stmt = (
                select(CheckpointModel)
                .where(CheckpointModel.thread_id == thread_id)
                .order_by(CheckpointModel.timestamp.desc())
                .limit(limit)
            )
            result = session.execute(stmt)
            models = result.scalars().all()

            return [self._model_to_checkpoint(model) for model in models]

    async def delete(self, thread_id: str, checkpoint_id: Optional[str] = None) -> None:
        """Delete checkpoint(s) from SQL database."""
        await self._ensure_initialized()

        if self.is_async:
            await self._delete_async(thread_id, checkpoint_id)
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._delete_sync, thread_id, checkpoint_id
            )

    async def _delete_async(self, thread_id: str, checkpoint_id: Optional[str]):
        """Helper for async delete."""
        async with self.session_maker() as session:  # type: ignore
            if checkpoint_id:
                stmt = delete(CheckpointModel).where(
                    CheckpointModel.checkpoint_id == checkpoint_id,
                    CheckpointModel.thread_id == thread_id,
                )
            else:
                stmt = delete(CheckpointModel).where(
                    CheckpointModel.thread_id == thread_id
                )

            await session.execute(stmt)
            await session.commit()

    def _delete_sync(self, thread_id: str, checkpoint_id: Optional[str]):
        """Helper for sync delete."""
        with self.session_maker() as session:  # type: ignore
            if checkpoint_id:
                stmt = delete(CheckpointModel).where(
                    CheckpointModel.checkpoint_id == checkpoint_id,
                    CheckpointModel.thread_id == thread_id,
                )
            else:
                stmt = delete(CheckpointModel).where(
                    CheckpointModel.thread_id == thread_id
                )

            session.execute(stmt)
            session.commit()

    async def clear_all(self) -> None:
        """Clear all checkpoints from SQL database."""
        await self._ensure_initialized()

        if self.is_async:
            await self._clear_all_async()
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._clear_all_sync)

    async def _clear_all_async(self):
        """Helper for async clear_all."""
        async with self.session_maker() as session:  # type: ignore
            stmt = delete(CheckpointModel)
            await session.execute(stmt)
            await session.commit()

    def _clear_all_sync(self):
        """Helper for sync clear_all."""
        with self.session_maker() as session:  # type: ignore
            stmt = delete(CheckpointModel)
            session.execute(stmt)
            session.commit()

    @staticmethod
    def _model_to_checkpoint(model: CheckpointModel) -> Checkpoint:
        """Convert SQLAlchemy model to Checkpoint object."""
        metadata = CheckpointMetadata(
            checkpoint_id=model.checkpoint_id,  # type: ignore
            thread_id=model.thread_id,  # type: ignore
            timestamp=model.timestamp,  # type: ignore
            node_name=model.node_name,  # type: ignore
            step=model.step,  # type: ignore
        )
        state = Checkpoint._deserialize_state(model.state)  # type: ignore
        return Checkpoint(metadata=metadata, state=state)

    async def close(self) -> None:
        """Close the database connection."""
        if self.is_async:
            await self.engine.dispose()  # type: ignore
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.engine.dispose)

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
