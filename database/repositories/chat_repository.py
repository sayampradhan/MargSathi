import logging
from typing import List, Dict
from database.database import get_db_session
from database.models.chat_history import ChatHistory

logger = logging.getLogger(__name__)

def save_chat(user_query: str, assistant_response: str):
    """Saves a single interaction to chat history."""
    with get_db_session() as session:
        if not session:
            return
        try:
            chat = ChatHistory(
                user_query=user_query,
                assistant_response=assistant_response
            )
            session.add(chat)
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")

def get_chat_history(limit: int = 50) -> List[Dict]:
    """Retrieves recent chat history."""
    with get_db_session() as session:
        if not session:
            return []
        try:
            chats = session.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(limit).all()
            return [{"user": c.user_query, "assistant": c.assistant_response, "time": c.created_at.isoformat()} for c in chats]
        except Exception as e:
            logger.error(f"Error retrieving chat history: {e}")
    return []

def delete_chat_history():
    """Deletes all chat history."""
    with get_db_session() as session:
        if not session:
            return
        try:
            session.query(ChatHistory).delete()
        except Exception as e:
            logger.error(f"Error deleting chat history: {e}")
