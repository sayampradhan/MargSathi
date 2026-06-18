import logging
import json
from typing import Optional, Dict
from datetime import datetime, timedelta
from database.database import get_db_session
from database.models.weather_cache import WeatherCache

logger = logging.getLogger(__name__)

CACHE_EXPIRY_HOURS = 24

def get_cached_weather(city: str, start_date: str, end_date: str) -> Optional[Dict]:
    """Retrieves cached weather if it hasn't expired."""
    with get_db_session() as session:
        if not session:
            return None
        try:
            weather = session.query(WeatherCache).filter(
                WeatherCache.city == city.lower(),
                WeatherCache.start_date == start_date,
                WeatherCache.end_date == end_date
            ).first()
            
            if weather:
                # Check expiry
                if datetime.utcnow() - weather.created_at < timedelta(hours=CACHE_EXPIRY_HOURS):
                    return json.loads(weather.forecast_json)
                else:
                    # Optional: Delete expired cache to keep DB clean
                    session.delete(weather)
                    logger.info(f"Expired weather cache removed for {city}")
        except Exception as e:
            logger.error(f"Error retrieving cached weather: {e}")
    return None

def save_weather_cache(city: str, start_date: str, end_date: str, forecast_data: Dict):
    """Saves weather data to the cache."""
    with get_db_session() as session:
        if not session:
            return
        try:
            # Upsert logic: delete old if exists, then insert
            existing = session.query(WeatherCache).filter(
                WeatherCache.city == city.lower(),
                WeatherCache.start_date == start_date,
                WeatherCache.end_date == end_date
            ).first()
            if existing:
                session.delete(existing)
                
            new_weather = WeatherCache(
                city=city.lower(),
                start_date=start_date,
                end_date=end_date,
                forecast_json=json.dumps(forecast_data)
            )
            session.add(new_weather)
        except Exception as e:
            logger.error(f"Error saving weather cache: {e}")
