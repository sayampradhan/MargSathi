import requests
import logging
from config import TRIPADVISOR_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "x-rapidapi-key": TRIPADVISOR_API_KEY,
    "x-rapidapi-host": "tripadvisor-scraper.p.rapidapi.com",
    "Content-Type": "application/json"
}


def search_hotel(hotel_name, city_name):
    """
    Searches TripAdvisor for a hotel by name and city.
    Returns the TripAdvisor URL for the best matching hotel, or None.
    """
    if not TRIPADVISOR_API_KEY:
        logger.warning("TRIPADVISOR_API_KEY not set. Skipping hotel search.")
        return None

    url = "https://tripadvisor-scraper.p.rapidapi.com/hotels/search"
    params = {
        "query": f"{hotel_name} {city_name}",
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )
        response.raise_for_status()
        data = response.json()

        # The API typically returns a list of results
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("link")
        elif isinstance(data, dict):
            results = data.get("results", data.get("data", []))
            if results and len(results) > 0:
                return results[0].get("link")

    except Exception as e:
        logger.error(f"Hotel Search API Error: {e}")

    return None


def get_hotel_details(tripadvisor_url):
    """
    Returns hotel details and reviews from TripAdvisor
    """
    if not TRIPADVISOR_API_KEY:
        logger.warning("TRIPADVISOR_API_KEY not set. Skipping hotel details.")
        return None

    url = "https://tripadvisor-scraper.p.rapidapi.com/hotels/detail"

    params = {
        "query": tripadvisor_url
    }

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:
        logger.error(f"Hotel Detail API Error: {e}")
        return None


def fetch_hotel_info(hotel_name, city_name):
    """
    Main entry point: searches for a hotel by name+city, then fetches full details.
    Returns the full TripAdvisor hotel detail dict, or None.
    """
    if not TRIPADVISOR_API_KEY:
        logger.warning("TRIPADVISOR_API_KEY not set. Skipping hotel lookup.")
        return None

    logger.info(f"Searching TripAdvisor for: {hotel_name} in {city_name}")

    # Step 1: Search for the hotel to get TripAdvisor URL
    hotel_url = search_hotel(hotel_name, city_name)

    if not hotel_url:
        # Fallback: try get_hotel_details directly with the name as query
        logger.info(f"Search returned no URL, trying direct detail query...")
        return get_hotel_details(f"{hotel_name} {city_name}")

    # Step 2: Get full details using the TripAdvisor URL
    logger.info(f"Found hotel URL: {hotel_url}")
    return get_hotel_details(hotel_url)