import requests
import os
from config import TRIPADVISOR_API_KEY

HEADERS = {
    "x-rapidapi-key": TRIPADVISOR_API_KEY,
    "x-rapidapi-host": "tripadvisor-scraper.p.rapidapi.com",
    "Content-Type": "application/json"
}


def get_hotel_details(tripadvisor_url):
    """
    Returns hotel details and reviews from TripAdvisor
    """

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
        print(f"Hotel API Error: {e}")
        return None