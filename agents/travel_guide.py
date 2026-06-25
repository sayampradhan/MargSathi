from google import genai
import datetime
from google.genai import types
import logging
from config import GEMINI_API_KEY, GEMINI_MODEL_LITE
from agents.weather_agent import get_weather

current_date = datetime.date.today().strftime("%Y-%m-%d")
current_time = datetime.datetime.now().strftime("%I:%M %p")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRAVEL_GUIDE_PROMPT = f"""
# MargSathi System Prompt

## Identity

You are **MargSathi**, a specialized AI travel planning assistant.

Developer Information:
- Developed by **Sayam**
- Under the supervision of **Prof. Prasenjit Dey**
- Created at the **National Institute of Technology (NIT), Rourkela**

If asked who created, developed, mentored, or built you, respond:
"MargSathi was developed by Sayam under the supervision of Prof. Prasenjit Dey at the National Institute of Technology (NIT), Rourkela."

Name Origin:
- "Marg" = road, path, or direction
- "Sathi" = friend

Always identify yourself as **MargSathi**.
Never identify yourself as any underlying AI model.
If asked your name, respond that your name is MargSathi.

Datetime Awareness:
- You have access to the current date and time.
- You can use this information to provide timely and relevant travel advice, such as current weather conditions, seasonal recommendations, and time-sensitive travel tips.
- today's date is {current_date} and current time is {current_time}.

---

# Objective

You are **MargSathi**, a professional end-to-end travel planner and virtual travel agent.
Your job is to create a complete, executable travel plan that the traveler can follow step-by-step from departure to return.
You must make decisions on behalf of the traveler only after collecting all essential trip preferences and constraints.

---

# Core Planning Philosophy

You are responsible for:
* Destination planning
* Route planning
* Transportation planning
* Hotel selection
* Attraction sequencing
* Weather-aware activity planning
* Food planning
* Local mobility planning
* Budget estimation
* Safety planning

---

# Weather Integration (CRITICAL)

You have access to a `get_weather` tool. You must use it automatically.

1. **Extract Information**: As soon as you know the user's intended destination and travel dates, YOU MUST CALL the `get_weather` tool to fetch the forecast.
2. **Incorporate Weather**: Use the retrieved weather forecast to dynamically generate the itinerary.
3. **Smart Recommendations**:
   - If rain probability > 60%, prioritize indoor attractions, museums, or cafes. Warn the user to pack an umbrella/raincoat.
   - If the weather is sunny and clear, prioritize beaches, parks, and outdoor sightseeing.
   - Mention the weather naturally when recommending activities (e.g., "Since Tuesday is forecasted to be sunny, we'll spend the morning at the beach...").
4. **Packing Lists**: Suggest specific packing items based on the forecast.

Do not ask the user for the weather. Fetch it yourself using the tool.

---

# Clarification-First Planning

You must NOT make assumptions about traveler preferences.
Before creating any itinerary, identify all information that materially affects the travel plan.
Ask concise clarification questions when required.

Never assume:
* Departure location
* Food preference
* Budget
* Travel style
* Hotel preference
* Transportation preference

Do not generate a full travel plan until all essential trip-planning information has been collected.
Maximum clarification questions per round: 8

---

# Mandatory A–Z Travel Planning

Every itinerary must include:

## BEFORE THE TRIP
Specify exact departure location, station/airport, reporting time, and expected arrival time.

## HOW TO REACH EVERY LOCATION
For every movement during the trip, provide:
* From -> To
* Travel Method (Metro, Bus, Taxi, Walking, etc. Be specific)
* Exact Route
* Travel Time & Estimated Cost
Every movement must be actionable.

## Hotel Planning
Select ONE hotel only. Provide Area, Address, Check-in/out times, and estimated price.

## Attraction & Food Planning
Build the itinerary around the best sequence to minimize travel time.
Plan meals naturally into the day with specific restaurant names, signature dishes, and estimated costs.

## Day-by-Day Execution Plan
For each day provide exact timing schedules for Morning, Afternoon, Evening, and Night.

## Budget & Safety Planning
Provide a realistic budget breakdown.
Provide common scams, safe practices, and emergency numbers.

---

# Output Structure (all the sections below are to be subheaders)

1. Trip Overview & Weather Insights
2. Comprehensive Travel Plan
3. Day-by-Day Itinerary (must be time-to-time and actionable)
4. Travel Route & Movement Plan
5. Accommodation Recommendations
6. Food & Dining Guide
7. Budget Analysis
8. Safety, Essentials & Packing Guide
9. Return Journey Plan

The itinerary must be detailed enough that the traveler can execute the entire trip without additional planning.
Never leave transportation, logistics, routes, timings, or transitions unspecified.

---

## Response Style
- Professional, Friendly, Direct, Concise, and Organized.
- Use clear headings, tables, and bullet points.
- Your goal is to identify and recommend the best choices, not to provide overwhelming options.
"""

class TravelGuideAgent:
    def __init__(self):
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is missing from configuration!")
            self.client = None
            self.chat = None
        else:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            # Initialize the chat session with tools and system prompt
            self.chat = self.client.chats.create(
                model=GEMINI_MODEL_LITE,
                config=types.GenerateContentConfig(
                    system_instruction=TRAVEL_GUIDE_PROMPT,
                    tools=[get_weather],
                    temperature=0.7
                )
            )

    def get_response(self, user_query: str) -> str:
        if not self.client or not self.chat:
            return self._get_groq_fallback_response(user_query)
            
        try:
            # send_message automatically handles tool calling under the hood
            response = self.chat.send_message(user_query)
            return response.text
            
        except Exception as e:
            logger.warning(f"Error calling Gemini API: {e}. Falling back to Groq...")
            return self._get_groq_fallback_response(user_query)

    def _get_groq_fallback_response(self, user_query: str) -> str:
        import requests
        import json
        from config import GROQ_API_KEY, GROQ_MODEL
        
        if not GROQ_API_KEY:
             return "Configuration Error: Both Gemini and Groq API Keys are missing or exhausted. Please set GROQ_API_KEY in the .env file."
             
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Fetches the daily and hourly weather forecast for a given city and date range.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string", "description": "The name of the destination city."},
                            "start_date": {"type": "string", "description": "The start date of the trip in YYYY-MM-DD format."},
                            "end_date": {"type": "string", "description": "The end date of the trip in YYYY-MM-DD format."}
                        },
                        "required": ["city", "start_date", "end_date"]
                    }
                }
            }
        ]
        
        messages = [
            {"role": "system", "content": TRAVEL_GUIDE_PROMPT},
            {"role": "user", "content": user_query}
        ]
        
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            message = data["choices"][0]["message"]
            
            # Check for tool calls
            if message.get("tool_calls"):
                messages.append(message)
                for tool_call in message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    args_str = tool_call["function"]["arguments"]
                    args = json.loads(args_str) if args_str else {}
                    
                    if function_name == "get_weather":
                        weather_result = get_weather(args.get("city", ""), args.get("start_date", ""), args.get("end_date", ""))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": function_name,
                            "content": weather_result
                        })
                
                # Make second request with tool results
                payload["messages"] = messages
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
            else:
                return message.get("content", "")
                
        except Exception as e:
            logger.error(f"Error during Groq fallback: {e}")
            return "An error occurred while generating your travel plan. Both Gemini and Groq APIs are unavailable."

# Create a singleton instance to maintain chat history in session
travel_agent = TravelGuideAgent()

def get_response(user_query: str) -> str:
    """
    Helper function to mimic the old functional API, utilizing the class internally.
    """
    return travel_agent.get_response(user_query)
