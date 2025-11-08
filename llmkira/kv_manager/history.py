# -*- coding: utf-8 -*-
"""
History Manager for tracking LLM request/response pairs
Stores conversation history with metadata for Web UI display
"""
import json
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from llmkira.kv_manager._base import KvManager


class HistoryEntry(BaseModel):
    """Single history entry for a request/response pair"""
    task_id: str = Field(..., description="Unique task identifier")
    timestamp: int = Field(default_factory=lambda: int(time.time()), description="Unix timestamp")
    platform: str = Field(..., description="Platform (telegram, discord, etc)")
    user_id: str = Field(..., description="User identifier")
    chat_id: str = Field(..., description="Chat/channel identifier")
    request: str = Field(..., description="User's request text")
    response: str = Field(..., description="LLM's response text")
    model: Optional[str] = Field(None, description="LLM model used")
    tool_calls: List[str] = Field(default=[], description="List of tools called")
    token_usage: Optional[int] = Field(None, description="Total tokens used")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create from dictionary"""
        return cls(**data)


class HistoryManager(KvManager):
    """Manages conversation history storage and retrieval"""

    def prefix(self, key: str) -> str:
        """Add history prefix to keys"""
        return f"kv:history:{key}"

    async def save_entry(self, entry: HistoryEntry, ttl: int = 60 * 60 * 24 * 30) -> bool:
        """
        Save a history entry
        :param entry: HistoryEntry to save
        :param ttl: Time to live in seconds (default 30 days)
        :return: Success status
        """
        try:
            # Save individual entry by task_id
            entry_key = f"entry:{entry.task_id}"
            await self.save_data(
                key=entry_key,
                value=json.dumps(entry.to_dict()),
                timeout=ttl
            )

            # Add to user's history index
            user_index_key = f"user:{entry.platform}:{entry.user_id}"
            await self._add_to_index(user_index_key, entry.task_id, entry.timestamp, ttl)

            # Add to global history index
            global_index_key = "global:all"
            await self._add_to_index(global_index_key, entry.task_id, entry.timestamp, ttl)

            return True
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to save history entry: {e}")
            return False

    async def _add_to_index(self, index_key: str, task_id: str, timestamp: int, ttl: int):
        """
        Add task_id to a sorted index
        Index format: {task_id}:{timestamp} stored as sorted set or list
        """
        try:
            # Read existing index
            index_data = await self.read_data(index_key)
            if index_data:
                index_list = json.loads(index_data)
            else:
                index_list = []

            # Add new entry with timestamp
            index_list.append({"task_id": task_id, "timestamp": timestamp})

            # Sort by timestamp (newest first)
            index_list.sort(key=lambda x: x["timestamp"], reverse=True)

            # Keep only last 1000 entries to prevent unbounded growth
            index_list = index_list[:1000]

            # Save updated index
            await self.save_data(
                key=index_key,
                value=json.dumps(index_list),
                timeout=ttl
            )
        except Exception as e:
            from loguru import logger
            logger.warning(f"Failed to update index {index_key}: {e}")

    async def get_entry(self, task_id: str) -> Optional[HistoryEntry]:
        """
        Get a specific history entry by task_id
        :param task_id: Task identifier
        :return: HistoryEntry or None
        """
        try:
            entry_key = f"entry:{task_id}"
            data = await self.read_data(entry_key)
            if data:
                return HistoryEntry.from_dict(json.loads(data))
            return None
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to get history entry {task_id}: {e}")
            return None

    async def get_user_history(
        self,
        platform: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[HistoryEntry]:
        """
        Get history for a specific user
        :param platform: Platform identifier
        :param user_id: User identifier
        :param limit: Maximum number of entries to return
        :param offset: Number of entries to skip
        :return: List of HistoryEntry objects
        """
        try:
            user_index_key = f"user:{platform}:{user_id}"
            index_data = await self.read_data(user_index_key)

            if not index_data:
                return []

            index_list = json.loads(index_data)

            # Apply pagination
            paginated_list = index_list[offset:offset + limit]

            # Fetch entries
            entries = []
            for item in paginated_list:
                entry = await self.get_entry(item["task_id"])
                if entry:
                    entries.append(entry)

            return entries
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to get user history: {e}")
            return []

    async def get_global_history(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[HistoryEntry]:
        """
        Get global history across all users
        :param limit: Maximum number of entries to return
        :param offset: Number of entries to skip
        :return: List of HistoryEntry objects
        """
        try:
            global_index_key = "global:all"
            index_data = await self.read_data(global_index_key)

            if not index_data:
                return []

            index_list = json.loads(index_data)

            # Apply pagination
            paginated_list = index_list[offset:offset + limit]

            # Fetch entries
            entries = []
            for item in paginated_list:
                entry = await self.get_entry(item["task_id"])
                if entry:
                    entries.append(entry)

            return entries
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to get global history: {e}")
            return []

    async def search_history(
        self,
        platform: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 50
    ) -> List[HistoryEntry]:
        """
        Search history with filters
        :param platform: Filter by platform
        :param user_id: Filter by user_id (requires platform)
        :param start_time: Filter entries after this timestamp
        :param end_time: Filter entries before this timestamp
        :param limit: Maximum number of results
        :return: List of matching HistoryEntry objects
        """
        # If user_id specified, get user-specific history
        if user_id and platform:
            entries = await self.get_user_history(platform, user_id, limit=limit)
        else:
            entries = await self.get_global_history(limit=limit * 2)  # Get more to filter

        # Apply time filters
        filtered_entries = []
        for entry in entries:
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if platform and entry.platform != platform:
                continue

            filtered_entries.append(entry)

            if len(filtered_entries) >= limit:
                break

        return filtered_entries


# Global instance
history_manager = HistoryManager()
