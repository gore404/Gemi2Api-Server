"""Session manager for persisting Gemini chat sessions."""
import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SESSION_STORAGE_PATH = os.environ.get("SESSION_STORAGE_PATH", os.path.join(os.path.dirname(__file__), "sessions"))


class SessionManager:
    """Manages Gemini chat sessions with persistence."""

    def __init__(self, storage_path: str = SESSION_STORAGE_PATH):
        self.storage_path = storage_path
        self.sessions: Dict[str, dict] = {}
        os.makedirs(storage_path, exist_ok=True)
        self._load_sessions()

    def _get_session_file(self, session_id: str) -> str:
        safe_id = session_id.replace("/", "_").replace("\\", "_")
        return os.path.join(self.storage_path, f"{safe_id}.json")

    def _load_sessions(self):
        """Load all sessions from disk."""
        try:
            for filename in os.listdir(self.storage_path):
                if filename.endswith(".json"):
                    session_id = filename[:-5]
                    filepath = os.path.join(self.storage_path, filename)
                    try:
                        with open(filepath, "r") as f:
                            self.sessions[session_id] = json.load(f)
                    except Exception as e:
                        logger.warning(f"Failed to load session {session_id}: {e}")
        except Exception as e:
            logger.warning(f"Failed to list sessions directory: {e}")

    def save_session(self, session_id: str, metadata: list, model: str = None, title: str = None):
        """Save or update a session."""
        now = datetime.now(timezone.utc).isoformat()
        if session_id in self.sessions:
            self.sessions[session_id]["metadata"] = metadata
            self.sessions[session_id]["updated_at"] = now
            if model:
                self.sessions[session_id]["model"] = model
        else:
            session_data = {
                "id": session_id,
                "metadata": metadata,
                "model": model,
                "title": title or f"Session {session_id[:8]}",
                "created_at": now,
                "updated_at": now,
            }
            self.sessions[session_id] = session_data

        filepath = self._get_session_file(session_id)
        try:
            with open(filepath, "w") as f:
                json.dump(self.sessions[session_id], f, indent=2)
            logger.info(f"Saved session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")

    def get_session(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            filepath = self._get_session_file(session_id)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                logger.info(f"Deleted session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
        return False

    def list_sessions(self, limit: int = 50) -> List[dict]:
        sessions_list = list(self.sessions.values())
        sessions_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return sessions_list[:limit]


# Singleton
session_manager = SessionManager()
