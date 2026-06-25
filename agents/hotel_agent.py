import logging
import requests
from typing import Optional, Dict
from config import GOOGLE_PLACES_API_KEY

logger = logging.getLogger(__name__)

def fetch_hotel_details(hotel_name: str, city_name: str) -> Optional[Dict]:
    """
    Fetches hotel details (rating, review snippet, photo URL) using Google Places API.
    If GOOGLE_PLACES_API_KEY is not configured or an error occurs, returns None.
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.warning("GOOGLE_PLACES_API_KEY not set. Cannot fetch hotel reviews/photos.")
        return None

    query = f"{hotel_name} {city_name}"
    
    # Step 1: Find Place ID
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    search_params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY
    }

    try:
        r = requests.get(search_url, params=search_params, timeout=10)
        r.raise_for_status()
        search_data = r.json()
        
        if not search_data.get("results"):
            logger.info(f"No Google Place found for hotel: {query}")
            return None
            
        place_id = search_data["results"][0]["place_id"]
        
        # We can extract rating and a photo reference directly from textsearch results
        place_info = search_data["results"][0]
        rating = place_info.get("rating")
        user_ratings_total = place_info.get("user_ratings_total")
        
        photo_url = None
        if "photos" in place_info and len(place_info["photos"]) > 0:
            photo_ref = place_info["photos"][0]["photo_reference"]
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={GOOGLE_PLACES_API_KEY}"

        # Step 2: Fetch detailed reviews (Optional, but makes it rich)
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "reviews",
            "key": GOOGLE_PLACES_API_KEY
        }
        
        details_r = requests.get(details_url, params=details_params, timeout=10)
        details_data = details_r.json()
        
        top_review = None
        if details_data.get("result") and "reviews" in details_data["result"]:
            reviews = details_data["result"]["reviews"]
            if len(reviews) > 0:
                # Get the highest rated helpful review or just the first one
                top_review = reviews[0].get("text")
                reviewer_name = reviews[0].get("author_name")
                if top_review and reviewer_name:
                    top_review = f'"{top_review}" — {reviewer_name}'
        
        return {
            "rating": rating,
            "user_ratings_total": user_ratings_total,
            "photo_url": photo_url,
            "top_review": top_review
        }

    except Exception as e:
        logger.error(f"Error fetching Google Places data for {query}: {e}")
        return None
