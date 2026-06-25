from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.database import Base

class ImageCache(Base):
    __tablename__ = "image_cache"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    place = Column(String, index=True, nullable=False, unique=True)
    
    images_json = Column(Text, nullable=False) # Store the JSON array of images
    
    created_at = Column(DateTime, default=datetime.utcnow)
