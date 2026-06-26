import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages the MongoDB Motor async client lifecycle."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Open connection to MongoDB Atlas."""
        logger.info("Connecting to MongoDB Atlas...")
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5,
            )
            self.db = self.client[settings.mongodb_db_name]

            # Verify the connection is live
            await self.client.admin.command("ping")
            logger.info(
                "MongoDB connection established — db: '%s'", settings.mongodb_db_name
            )
        except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
            logger.error("MongoDB connection failed: %s", exc)
            raise

    async def disconnect(self) -> None:
        """Close the MongoDB connection cleanly."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    def get_db(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            raise RuntimeError("Database not initialised. Call connect() first.")
        return self.db

    # ── Collection helpers ────────────────────────────────────────────────────
    @property
    def users(self):
        return self.db["users"]

    @property
    def patients(self):
        return self.db["patients"]

    @property
    def diagnoses(self):
        return self.db["diagnoses"]

    @property
    def medical_records(self):
        return self.db["medical_records"]

    @property
    def audit_logs(self):
        return self.db["audit_logs"]

    @property
    def chat_sessions(self):
        return self.db["chat_sessions"]


# ── Singleton ─────────────────────────────────────────────────────────────────
db_manager = DatabaseManager()


def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency — returns the active database handle."""
    return db_manager.get_db()