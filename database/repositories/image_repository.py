import logging
import json
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from database.database import get_db_session
from database.models.image_cache import ImageCache

logger = logging.getLogger(__name__)

CACHE_EXPIRY_DAYS = 30

def get_cached_images(place: str) -> Optional[List[Dict]]:
    """Retrieves cached images if they haven't expired."""
    with get_db_session() as session:
        if not session:
            return None
        try:
            img_cache = session.query(ImageCache).filter(
                ImageCache.place == place.lower()
            ).first()
            
            if img_cache:
                if datetime.utcnow() - img_cache.created_at < timedelta(days=CACHE_EXPIRY_DAYS):
                    return json.loads(img_cache.images_json)
                else:
                    session.delete(img_cache)
                    logger.info(f"Expired image cache removed for {place}")
        except Exception as e:
            logger.error(f"Error retrieving cached image: {e}")
    return None

def save_image_cache(place: str, images_list: List[Dict]):
    """Saves image search results to the cache."""
    with get_db_session() as session:
        if not session:
            return
        try:
            existing = session.query(ImageCache).filter(
                ImageCache.place == place.lower()
            ).first()
            if existing:
                session.delete(existing)
                
            new_cache = ImageCache(
                place=place.lower(),
                images_json=json.dumps(images_list)
            )
            session.add(new_cache)
        except Exception as e:
            logger.error(f"Error saving image cache: {e}")
