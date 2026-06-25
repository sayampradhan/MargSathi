import logging
from typing import Optional, Dict
import hashlib
import json
from database.database import get_db_session
from database.models.trip_cache import TripCache

logger = logging.getLogger(__name__)

def generate_cache_key(destination: str, departure: str, start_date: str, end_date: str, budget: str, travel_type: str, currency: str = "USD") -> str:
    """Generates a deterministic hash key for trip caching."""
    # Normalize inputs
    components = [
        str(destination).strip().lower() if destination else "",
        str(departure).strip().lower() if departure else "",
        str(start_date).strip() if start_date else "",
        str(end_date).strip() if end_date else "",
        str(budget).strip().lower() if budget else "",
        str(travel_type).strip().lower() if travel_type else "",
        str(currency).strip().upper() if currency else "USD"
    ]
    raw_key = "|".join(components)
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

def get_cached_trip(cache_key: str) -> Optional[Dict]:
    """Retrieves a cached trip response by cache key."""
    with get_db_session() as session:
        if not session:
            return None
        try:
            trip = session.query(TripCache).filter(TripCache.cache_key == cache_key).first()
            if trip:
                return {
                    "response": trip.response,
                    "extracted_names": trip.get_extracted_names()
                }
        except Exception as e:
            logger.error(f"Error retrieving cached trip: {e}")
    return None

def save_trip_cache(cache_key: str, query: str, response: str, extracted_names: dict,
                    destination: str = None, departure: str = None,
                    start_date: str = None, end_date: str = None,
                    budget: str = None, travel_type: str = None, currency: str = None):
    """Saves a trip response to the cache."""
    with get_db_session() as session:
        if not session:
            return
        try:
            # Check if it already exists to avoid unique constraint failure
            existing = session.query(TripCache).filter(TripCache.cache_key == cache_key).first()
            if existing:
                return
            
            new_trip = TripCache(
                cache_key=cache_key,
                query=query,
                response=response,
                destination=destination,
                departure=departure,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                travel_type=travel_type
            )
            new_trip.set_extracted_names(extracted_names)
            session.add(new_trip)
        except Exception as e:
            logger.error(f"Error saving trip cache: {e}")
