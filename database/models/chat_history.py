from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
