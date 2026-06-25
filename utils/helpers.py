import json
import urllib.parse
from google import genai
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL_DEFAULT, GROQ_API_KEY, GROQ_MODEL

def extract_names_with_groq(extraction_prompt: str) -> dict:
    """Fallback extraction using Groq's high-speed API if Gemini fails."""
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY not set for fallback.")
        return {"is_trip_plan": False, "destinations": [], "hotel": [], "hotel_city": [], "foods": []}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "user", "content": extraction_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        parsed = json.loads(content)
        return {
            "is_trip_plan": parsed.get("is_trip_plan", False),
            "destinations": parsed.get("destinations", []),
            "hotel": parsed.get("hotel", []),
            "hotel_city": parsed.get("hotel_city", []),
            "foods": parsed.get("foods", []),
            "restaurants": parsed.get("restaurants", []),
        }
    except Exception as e:
        print(f"Error during JSON extraction via Groq fallback: {e}")
        return {"is_trip_plan": False, "destinations": [], "hotel": [], "hotel_city": [], "foods": [], "restaurants": []}

def extract_names(itinerary_text: str) -> dict:
    """
    Extract destinations, hotels, and food items from the travel itinerary
    using the Gemini model, with an automatic fallback to Groq.
    """
    extraction_prompt = f"""
    Analyze the text and extract the following information.

    First, determine if the text provided is a comprehensive travel itinerary/plan OR if it is just a conversational message/follow-up question. Set "is_trip_plan" to true ONLY if the text contains a detailed travel plan.

    Return ONLY valid JSON.

    {{
        "is_trip_plan": false,
        "destinations": [],
        "hotel": [],
        "hotel_city": [],
        "foods": [],
        "restaurants": []
    }}

    Rules:
    - is_trip_plan = true if the text is a detailed travel itinerary. false if it's just a question or conversation.
    - destinations = stations, busstands, tourist places, attractions, landmarks, beaches, temples, museums etc. (every place that is included in the travel plan no matter if it is railway station or bustand or even airport)
    - hotel = hotel name only (eg., "Taj Hotel" for "Taj Hotel in Panaji")
    - hotel city = name of the city of the hotel (eg., "Panaji" for "Taj Hotel in Panaji")
    - foods = local dish names only (e.g., "Pav Bhaji", "Chicken Biryani" etc.)
    - restaurants = restaurant names, along with the city name if available (e.g., "Taj Mahal Restaurant, Delhi")
    - remove duplicates
    - do not include the place of departure
    - do not include explanations

    Itinerary:

    {itinerary_text}
    """

    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set in configuration. Falling back to Groq directly.")
        return extract_names_with_groq(extraction_prompt)

    client = genai.Client(api_key=GEMINI_API_KEY)

    import time
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_DEFAULT,
                contents=extraction_prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "is_trip_plan": {
                                "type": "BOOLEAN"
                            },
                            "destinations": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "hotel": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "hotel_city": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "foods": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "restaurants": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        }
                    }
                }
            )

            if not response or not response.text:
                raise ValueError("Empty response from Gemini")

            data = json.loads(response.text)

            return {
                "is_trip_plan": data.get("is_trip_plan", False),
                "destinations": data.get("destinations", []),
                "hotel": data.get("hotel", []),
                "hotel_city": data.get("hotel_city", []),
                "foods": data.get("foods", []),
                "restaurants": data.get("restaurants", [])
            }
        except Exception as e:
            print(f"Attempt {attempt + 1} - Error during JSON extraction via Gemini: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("Gemini exhausted. Falling back to Groq...")
                return extract_names_with_groq(extraction_prompt)


def hotel_booking(hotel_name: str, city_name: str) -> str:
    """
    Generate a booking.com search URL for the given hotel and city.
    """
    if not hotel_name or not city_name:
        return ""

    query = urllib.parse.quote(f"{hotel_name} {city_name}")
    return f"https://www.booking.com/searchresults.html?ss={query}"
