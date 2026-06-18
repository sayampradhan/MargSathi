from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database.database import Base

class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    
    forecast_json = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
