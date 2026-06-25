import requests
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from config import TRIPADVISOR_API_KEY, FALLBACK_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "x-rapidapi-key": TRIPADVISOR_API_KEY,
    "x-rapidapi-host": "tripadvisor-scraper.p.rapidapi.com",
    "Content-Type": "application/json"
}

def make_tripadvisor_request(url, params):
    import time
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code in [403, 429]:
            logger.warning(f"Primary API key failed with {status_code}. Retrying with fallback key...")
            fallback_headers = HEADERS.copy()
            fallback_headers['x-rapidapi-key'] = FALLBACK_API_KEY
            time.sleep(1)
            response = requests.get(url, headers=fallback_headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        raise e


def search_restaurant(query: str) -> Optional[Dict]:
    """
    Searches TripAdvisor for a restaurant by name.
    Returns the first matching RESTAURANT entity with its details, or None.
    """
    if not TRIPADVISOR_API_KEY:
        logger.warning("TRIPADVISOR_API_KEY not set. Skipping restaurant search.")
        return None

    url = "https://tripadvisor-scraper.p.rapidapi.com/restaurants/search"
    params = {
        "query": query,
    }

    import time
    time.sleep(1) # Add delay to prevent rate limiting
    try:
        data = make_tripadvisor_request(url, params)

        if isinstance(data, str):
            try:
                import json
                data = json.loads(data)
            except Exception:
                logger.error(f"Unexpected API response format (string): {data[:100]}")
                return None

        if not isinstance(data, dict):
            logger.error(f"Unexpected API response type: {type(data)}")
            return None

        results = data.get("results", [])
        if not results:
            return None

        # Prefer actual restaurant entities over city/state results
        for result in results:
            if isinstance(result, dict) and result.get("is_tripadvisor_entity") and result.get("place_type") == "RESTAURANT":
                return {
                    "name": result.get("name", ""),
                    "link": result.get("link", ""),
                    "featured_image": result.get("featured_image", ""),
                    "coordinates": result.get("coordinates", {}),
                    "parent_location": result.get("parent_location", {}).get("name", ""),
                    "tripadvisor_entity_id": result.get("tripadvisor_entity_id"),
                }

        # Fallback: return the first result even if it's a city
        first = results[0]
        if not isinstance(first, dict):
            return None

        return {
            "name": first.get("name", ""),
            "link": first.get("link", ""),
            "featured_image": first.get("featured_image", ""),
            "coordinates": first.get("coordinates", {}),
            "parent_location": first.get("parent_location", {}).get("name", ""),
            "tripadvisor_entity_id": first.get("tripadvisor_entity_id"),
        }

    except Exception as e:
        logger.error(f"Restaurant Search API Error for '{query}': {e}")

    return None


def fetch_restaurants(restaurant_names: List[str], max_workers: int = 4) -> List[Dict]:
    """
    Fetches TripAdvisor data for multiple restaurants concurrently.
    Returns a list of restaurant dicts with image, coordinates, and TripAdvisor link.
    """
    if not TRIPADVISOR_API_KEY or not restaurant_names:
        return []

    logger.info(f"Searching TripAdvisor for {len(restaurant_names)} restaurants...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(search_restaurant, restaurant_names))

    valid = [r for r in results if r]
    logger.info(f"Found {len(valid)} restaurants on TripAdvisor out of {len(restaurant_names)} searched.")
    return valid
