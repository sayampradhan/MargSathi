import logging
import requests
import logging
import requests
from typing import List, Dict, Optional
from database.repositories import get_cached_images, save_image_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_wikimedia_images(query: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Searches Wikimedia Commons for images related to the query.
    Returns the top matching image URLs directly from the API.
    """
    url = "https://commons.wikimedia.org/w/api.php"
    
    # We use a higher limit in the API request, then filter for valid extensions,
    # and return up to `limit` valid results.
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,  # File namespace
        "gsrlimit": max(limit * 2, 10), # Fetch extra to account for filtering
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }

    headers = {
        "User-Agent": "MargSathiBot/1.0"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f"Error fetching from Wikimedia for '{query}': {e}")
        return []

    results = []
    pages = data.get("query", {}).get("pages", {})

    # The pages dictionary is not ordered by relevance guarantee, but generally
    # search results are somewhat ordered. We will just grab valid images.
    for page in pages.values():
        title = page.get("title", "")
        
        if not title.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue

        image_info = page.get("imageinfo", [])
        if not image_info:
            continue
            
        url_info = image_info[0].get("url")
        if not url_info:
            continue

        results.append({
            "source": "Wikimedia Commons",
            "title": title,
            "url": url_info
        })
        
        if len(results) >= limit:
            break

    return results

def get_best_images(query: str, limit: int = 5) -> Dict:
    """
    Wrapper function that directly returns images without LLM ranking.
    """
    cached_images = get_cached_images(query)
    if cached_images:
        logger.info(f"Image cache hit for {query}")
        return {
            "query": query,
            "total_candidates": len(cached_images),
            "results": cached_images
        }
        
    candidates = search_wikimedia_images(query=query, limit=limit)
    if candidates:
        save_image_cache(query, candidates)
    
    return {
        "query": query,
        "total_candidates": len(candidates),
        "results": candidates
    }

def fetch_destination_image(place: str) -> Optional[Dict]:
    """
    Fetches destination images for concurrent loading.
    """
    try:
        images = get_best_images(place, limit=1) # Usually just need 1 image per place
        if images and images.get("results"):
            return {
                "place": place,
                "image": images["results"]
            }
    except Exception as e:
        logger.error(f"Error fetching image for {place}: {e}")
    return None

def fetch_food_images(food: str) -> Optional[Dict]:
    """
    Fetches food images.
    """
    search_query = food  # Removing ' food' suffix as it breaks wikimedia search
    try:
        images = get_best_images(search_query, limit=2) # Fetch 2 images for food to give variety
        if images and images.get("results"):
            return {
                "food": food,
                "image": images["results"]
            }
    except Exception as e:
        logger.error(f"Error fetching image for {food}: {e}")
    return None