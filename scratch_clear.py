from database.database import get_db_session
from database.models.trip_cache import TripCache
from sqlalchemy import text

def clear_cache():
    with get_db_session() as session:
        if not session:
            print("DB NOT AVAILABLE")
            return
        
        session.query(TripCache).delete()
        print("Cache cleared")
            
clear_cache()
