from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
import json
from database.database import Base

class TripCache(Base):
    __tablename__ = "trip_cache"

    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String, unique=True, index=True, nullable=False)
    
    # Input parameters
    query = Column(Text, nullable=False)
    destination = Column(String, index=True, nullable=True)
    departure = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    budget = Column(String, nullable=True)
    travel_type = Column(String, nullable=True)
    
    # Generated Outputs
    response = Column(Text, nullable=False)
    extracted_names_json = Column(Text, nullable=True) # Storing the names dict
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def set_extracted_names(self, data: dict):
        self.extracted_names_json = json.dumps(data)

    def get_extracted_names(self) -> dict:
        if self.extracted_names_json:
            return json.loads(self.extracted_names_json)
        return {}
