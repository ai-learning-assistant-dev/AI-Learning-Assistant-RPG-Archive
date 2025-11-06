import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from config.settings import settings


class StoreService:

    def __init__(self):
        """Initialize the store service."""
        file_path = Path(settings.database_path)
        file_path.touch(exist_ok=True)
        self._db_path = "sqlite+aiosqlite:///" + settings.database_path

    async def init(self) -> None:
        """Idempotently创建表: 如果不存在则创建 (使用32位UUID主键)。不进行迁移或删除。"""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS session (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation (
                    id TEXT PRIMARY KEY,
                    parent_cid TEXT DEFAULT '',
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES session(id) ON DELETE CASCADE
                );
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_conversation_session_id
                ON conversation (session_id);
                """
            )
            await db.commit()

    # ------------------------- Session CRUD -------------------------
    async def create_session(self, title: str) -> str:
        """Insert a new session and return its UUID (hex)."""
        session_id = uuid.uuid4().hex
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO session (id, title) VALUES (?, ?)", (session_id, title)
            )
            await db.commit()
            return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single session by id."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, title, created_at FROM session WHERE id = ?", (session_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def list_sessions(
        self, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List sessions with pagination."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, title, created_at FROM session ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def update_session(self, session_id: str, title: str) -> bool:
        """Update session title. Returns True if a row was updated."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "UPDATE session SET title = ? WHERE id = ?", (title, session_id)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session (cascades to conversations)."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("DELETE FROM session WHERE id = ?", (session_id,))
            await db.execute(
                "DELETE FROM conversation WHERE session_id = ?", (session_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    # ---------------------- Conversation CRUD ----------------------
    async def create_conversation(
        self, session_id: str, content: str, type: str, parent_cid: str = ""
    ) -> str:
        """Add a conversation entry for a session and return its UUID."""
        conv_id = uuid.uuid4().hex
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT INTO conversation (id, parent_cid, session_id, content, type) VALUES (?, ?, ?, ?, ?)",
                (conv_id, parent_cid, session_id, content, type),
            )
            await db.commit()
            return conv_id

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single conversation by id."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, session_id, content, type, created_at FROM conversation WHERE id = ?",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            # Decode bytes back to string for convenience
            if isinstance(data["content"], (bytes, bytearray)):
                with suppress(KeyError):
                    data["content"] = data["content"].decode("utf-8")
            return data

    async def update_conversation(self, conversation_id: str, content: str) -> bool:
        """Update conversation content. Returns True if a row was updated."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "UPDATE conversation SET content = ? WHERE id = ?",
                (content, conversation_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def list_conversations(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List conversations for a given session."""
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT id, session_id, content, type, created_at
                FROM conversation
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ? OFFSET ?
                """,
                (session_id, limit, offset),
            )
            rows = await cursor.fetchall()
            result: List[Dict[str, Any]] = []
            for r in rows:
                item = dict(r)
                if isinstance(item["content"], (bytes, bytearray)):
                    with suppress(KeyError):
                        item["content"] = item["content"].decode("utf-8")
                result.append(item)
            return result

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by id."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "DELETE FROM conversation WHERE id = ?", (conversation_id,)
            )
            await db.commit()
            return cursor.rowcount > 0


store_service = StoreService()
