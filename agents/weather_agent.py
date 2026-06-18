import logging
import requests
from urllib.parse import quote
from typing import List, Dict, Optional
import json
from collections import defaultdict
from datetime import datetime
from database.repositories import get_cached_weather, save_weather_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for the UI to consume later
WEATHER_CACHE = {}
LAST_FETCHED_WEATHER = None

def get_weather_emoji(code: int) -> str:
    """Maps Open-Meteo WMO weather codes to emojis."""
    if code == 0:
        return "☀️" # Clear sky
    elif code in [1, 2, 3]:
        return "⛅" # Mainly clear, partly cloudy, and overcast
    elif code in [45, 48]:
        return "🌫️" # Fog
    elif code in [51, 53, 55, 56, 57]:
        return "🌧️" # Drizzle
    elif code in [61, 63, 65, 66, 67]:
        return "🌧️" # Rain
    elif code in [71, 73, 75, 77]:
        return "❄️" # Snow
    elif code in [80, 81, 82]:
        return "🌦️" # Rain showers
    elif code in [85, 86]:
        return "🌨️" # Snow showers
    elif code in [95, 96, 99]:
        return "⛈️" # Thunderstorm
    return "🌡️"


def format_weather(daily: Dict, hourly: Dict) -> Dict:
    """
    Formats the daily and hourly weather data from Open-Meteo into a structured dictionary.
    """
    forecast = {"daily": [], "hourly": defaultdict(list)}
    
    # Process daily data
    try:
        if daily:
            for i in range(len(daily.get("time", []))):
                forecast["daily"].append({
                    "date": daily["time"][i],
                    "max_temp_celsius": daily["temperature_2m_max"][i],
                    "min_temp_celsius": daily["temperature_2m_min"][i],
                    "rain_probability_percent": daily["precipitation_probability_max"][i],
                    "weather_code": daily["weather_code"][i],
                    "emoji": get_weather_emoji(daily["weather_code"][i])
                })
    except Exception as e:
        logger.error(f"Error formatting daily weather: {e}")

    # Process hourly data
    try:
        if hourly:
            for i in range(len(hourly.get("time", []))):
                time_str = hourly["time"][i]
                # Open-Meteo returns time as "YYYY-MM-DDTHH:MM"
                date_part = time_str.split("T")[0]
                hour_part = time_str.split("T")[1]
                
                forecast["hourly"][date_part].append({
                    "time": hour_part,
                    "temp_celsius": hourly["temperature_2m"][i],
                    "rain_probability_percent": hourly["precipitation_probability"][i],
                    "wind_speed_kmh": hourly["wind_speed_10m"][i],
                    "weather_code": hourly["weather_code"][i],
                    "emoji": get_weather_emoji(hourly["weather_code"][i])
                })
    except Exception as e:
        logger.error(f"Error formatting hourly weather: {e}")
        
    return forecast


def get_weather(city: str, start_date: str, end_date: str) -> str:
    """
    Fetches the daily and hourly weather forecast for a given city and date range.
    Use this tool whenever you have the user's destination and travel dates.

    Args:
        city: The name of the destination city.
        start_date: The start date of the trip in YYYY-MM-DD format.
        end_date: The end date of the trip in YYYY-MM-DD format.
    
    Returns:
        A JSON string containing the daily weather forecast (max/min temp, rain probability, etc.)
        or an error message if the weather could not be fetched.
    """
    global LAST_FETCHED_WEATHER
    
    # Check if we already have it to avoid duplicate calls in the same session run
    cache_key = f"{city}_{start_date}_{end_date}"
    if cache_key in WEATHER_CACHE:
        LAST_FETCHED_WEATHER = {"city": city, "forecast": WEATHER_CACHE[cache_key]}
        return json.dumps({
            "city": city,
            "forecast": WEATHER_CACHE[cache_key]["daily"] # Return simplified version to LLM
        })

    # Check PostgreSQL L2 cache
    cached_weather = get_cached_weather(city, start_date, end_date)
    if cached_weather:
        logger.info(f"Weather cache hit for {city}")
        WEATHER_CACHE[city.lower()] = cached_weather
        WEATHER_CACHE[cache_key] = cached_weather
        LAST_FETCHED_WEATHER = {"city": city, "forecast": cached_weather}
        return json.dumps({
            "city": city,
            "forecast": cached_weather["daily"]
        })

    encoded_city = quote(city)

    # 1. Get Coordinates
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1"

    try:
        geo_response = requests.get(geo_url, timeout=10)
        geo_response.raise_for_status()
        geo = geo_response.json()
    except Exception as e:
        logger.error(f"Geocoding API failed for '{city}': {e}")
        return json.dumps({"error": f"Failed to find location coordinates for {city}."})

    if "results" not in geo or not geo["results"]:
        logger.warning(f"No geocoding results found for city: {city}")
        return json.dumps({"error": f"Location '{city}' not found."})

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    # 2. Get Weather (Daily + Hourly)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "hourly": "temperature_2m,precipitation_probability,weather_code,wind_speed_10m",
        "timezone": "auto"
    }

    try:
        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params=params,
            timeout=20
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
    except Exception as e:
        logger.error(f"Weather API failed for '{city}': {e}")
        return json.dumps({"error": f"Failed to fetch weather forecast for {city}."})

    if "daily" not in weather_data:
        logger.warning(f"No daily weather data returned for {city}")
        return json.dumps({"error": f"No daily weather data available for {city} for the selected dates."})

    forecast = format_weather(weather_data.get("daily", {}), weather_data.get("hourly", {}))
    
    # Cache the rich data for the UI
    WEATHER_CACHE[city.lower()] = forecast # Also map by city for UI lookup
    WEATHER_CACHE[cache_key] = forecast
    
    # Update global reference so UI can easily pull the very last fetched weather
    LAST_FETCHED_WEATHER = {"city": city, "forecast": forecast}

    # Save to PostgreSQL L2 Cache
    save_weather_cache(city, start_date, end_date, forecast)

    # Return full data to the LLM so it can plan hourly activities
    return json.dumps({
        "city": city,
        "forecast": forecast
    })
