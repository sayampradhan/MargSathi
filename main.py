import streamlit as st
import datetime
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import refactored agents and utils
from agents.travel_guide import get_response
from agents.image_agent import fetch_destination_image
import agents.weather_agent
from utils.helpers import extract_names, hotel_booking
from config import GEMINI_API_KEY
from database.database import init_db
from database.repositories import generate_cache_key, get_cached_trip, save_trip_cache, save_chat

# -------------------------------------------------
# Page Config
# -------------------------------------------------
st.set_page_config(
    page_title="MargSathi",
    page_icon="🧭",
    layout="wide"
)

@st.cache_resource
def setup_db():
    init_db()

setup_db()

# -------------------------------------------------
# Custom CSS
# -------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f8fafc;
}

.title {
    text-align:center;
    font-size:42px;
    font-weight:700;
    color:#0f172a;
}

.subtitle {
    text-align:center;
    color:#64748b;
    margin-bottom:20px;
}

.creator {
    text-align:center;
    color:#334155;
    font-size:15px;
}

.stChatMessage {
    border-radius:15px;
}

/* Hourly Weather Scroller */
.hourly-scroller {
    display: flex;
    overflow-x: auto;
    gap: 15px;
    padding: 15px 5px;
    scroll-behavior: smooth;
}
.hourly-scroller::-webkit-scrollbar {
    height: 6px;
}
.hourly-scroller::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}
.hourly-card {
    flex: 0 0 auto;
    width: 100px;
    background: white;
    border-radius: 12px;
    padding: 15px 10px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #f1f5f9;
}
.hourly-time {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 5px;
    font-weight: 600;
}
.hourly-emoji {
    font-size: 28px;
    margin: 8px 0;
}
.hourly-temp {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
}
.hourly-rain {
    font-size: 12px;
    color: #3b82f6;
    margin-top: 5px;
    font-weight: 600;
}

/* Daily Summary Card */
.daily-summary {
    background: linear-gradient(135deg, #38bdf8, #0284c7);
    color: white;
    border-radius: 16px;
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(2, 132, 199, 0.2);
}
.daily-info h3 {
    margin: 0 0 5px 0;
    font-size: 24px;
    color: white !important;
}
.daily-info p {
    margin: 0;
    opacity: 0.9;
    font-size: 16px;
}
.daily-emoji {
    font-size: 48px;
}
.daily-stats {
    display: flex;
    gap: 20px;
    background: rgba(255,255,255,0.2);
    padding: 10px 20px;
    border-radius: 12px;
}
.stat-box {
    text-align: center;
}
.stat-val {
    font-size: 20px;
    font-weight: 700;
}
.stat-label {
    font-size: 12px;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Header
# -------------------------------------------------
st.markdown(
    """
    <div class='title'>
        🧭 MargSathi
    </div>
    <div class='subtitle'>
        Your Intelligent Travel Companion
    </div>
    <div class='creator'>
        Developed by <b>Sayam</b><br>
        Under the supervision of <b>Prof. Prasenjit Dey</b><br>
        National Institute of Technology Rourkela
    </div>
    <hr>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.markdown(
    """
    <div class='title'>
        🧭 MargSathi
    </div>
    <div class='subtitle'>
        Your Intelligent Travel Companion
    </div>
    <hr>
    """,
    unsafe_allow_html=True
    )

    st.header("Trip Preferences")

    departure = st.text_input("Departure")
    destination = st.text_input("Destination")

    today = datetime.datetime.now()
    start_date = st.date_input("Start Date", today, format="YYYY.MM.DD")
    end_date = st.date_input("End Date", value=today + timedelta(days=2), format="YYYY.MM.DD")

    budget = st.selectbox("Budget", ["Budget", "Mid-range", "Luxury"])
    mode_of_transport = st.selectbox("Mode of Transport", ["Bus", "Train", "Flight"])
    food_preference = st.selectbox("Food Preferences", ["Pure Vegetarian (no onion and garlic)", "Vegetarian", "Non-Vegetarian"])
    food_allergy = st.selectbox("Food Allergy", ["Yes", "No"])
    travelers = st.selectbox("Travel Type", ["Solo", "Couple", "Group", "Family", "Other"])
    further_preferences = st.selectbox("Further preferences", ["Yes", "No"])

    if st.button("Generate Trip Plan"):
        query = f"""
        Plan a trip to {destination}

        Departure: {departure},
        Start date: {start_date},
        End date: {end_date},
        Budget: {budget},
        Travel type: {travelers},
        Food preferences: {food_preference},
        Food allergies: {food_allergy},
        Mode of transport to destination: {mode_of_transport},
        Further preferences to ask: {further_preferences}

        If further preferences is "No", then don't ask further questions and go straight on and generate the full trip plan.

        Create a detailed itinerary.
        """

        if "messages" not in st.session_state:
            st.session_state.messages = []
            
        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.sidebar_query = query
        st.session_state.trip_params = {
            "destination": destination,
            "departure": departure,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "budget": budget,
            "travel_type": travelers
        }
        st.rerun()

# -------------------------------------------------
# Session State & Main Chat
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Where would you like to travel today?")

# Handle both prompt and sidebar query
active_query = None
trip_params = None
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    active_query = prompt
elif "sidebar_query" in st.session_state:
    active_query = st.session_state.sidebar_query
    trip_params = st.session_state.get("trip_params")
    del st.session_state.sidebar_query
    if "trip_params" in st.session_state:
        del st.session_state.trip_params
    # Note: We don't echo the sidebar query visually in the chat to avoid clutter

if active_query:
    if not GEMINI_API_KEY:
        st.error("API Key not found! Please check your Streamlit secrets or environment variables.")
    else:
        with st.chat_message("assistant"):
            # Step 1: Agent Generation
            with st.spinner("Planning your journey..."):
                # Clear the old fetched weather from this state just in case
                agents.weather_agent.LAST_FETCHED_WEATHER = None
                
                if trip_params:
                    cache_key = generate_cache_key(**trip_params)
                else:
                    import hashlib
                    cache_key = hashlib.sha256(active_query.encode('utf-8')).hexdigest()
                
                cached_trip = get_cached_trip(cache_key)
                if cached_trip:
                    logger.info("Trip cache hit!")
                    response = cached_trip["response"]
                    names = cached_trip["extracted_names"]
                else:
                    logger.info("Trip cache miss. Calling Gemini...")
                    response = get_response(active_query)
                    names = extract_names(response)
                    save_trip_cache(
                        cache_key=cache_key,
                        query=active_query,
                        response=response,
                        extracted_names=names,
                        **(trip_params or {})
                    )

            # Step 2: Destination Images
            with st.spinner("Loading destination gallery..."):
                valid_results = []
                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(fetch_destination_image, names.get("destinations", [])))

                valid_results = [r for r in results if r]

                if valid_results:
                    st.subheader("📍 Destinations")
                    gallery_html = """
                    <style>
                    .scrolling-gallery {
                        display: flex;
                        overflow-x: auto;
                        gap: 20px;
                        padding: 10px;
                        scroll-behavior: smooth;
                    }
                    .scrolling-gallery::-webkit-scrollbar {
                        height: 8px;
                    }
                    .scrolling-gallery::-webkit-scrollbar-thumb {
                        background: #94a3b8;
                        border-radius: 10px;
                    }
                    .image-card {
                        flex: 0 0 auto;
                        width: 280px;
                        background: white;
                        border-radius: 18px;
                        overflow: hidden;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    }
                    .image-card img {
                        width: 100%;
                        height: 200px;
                        object-fit: cover;
                    }
                    .image-title {
                        padding: 12px;
                        text-align: center;
                        font-weight: 600;
                        font-size: 16px;
                    }
                    </style>
                    <div class="scrolling-gallery">
                    """

                    for result in valid_results:
                        place = result["place"]
                        images = result.get("image", [])
                        if not images:
                            continue

                        img_url = images[0].get("url")
                        if not img_url:
                            continue

                        gallery_html += f"""
                        <div class="image-card">
                            <img src="{img_url}">
                            <div class="image-title">{place}</div>
                        </div>
                        """

                    gallery_html += "</div>"
                    st.html(gallery_html)
                    st.markdown("---")

            # Step 3: Core Itinerary
            st.markdown(response)


            # Step 4: Hotel Bookings
            hotel_names = names.get("hotel", [])
            hotel_cities = names.get("hotel_city", [])

            if hotel_names and hotel_cities:
                hotel_name = hotel_names[0]
                city_name = hotel_cities[0]
                booking_url = hotel_booking(hotel_name, city_name)

                st.subheader("🛏️ Book Hotel")
                st.write(f"**Hotel:** {hotel_name}")
                st.write(f"**City:** {city_name}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(
                        f"""
                        <a href="{booking_url}" target="_blank" style="
                            display:block;
                            text-align:center;
                            background-color:#ffa421 !important;
                            color:yellow !important;
                            padding:14px;
                            border-radius:12px;
                            text-decoration:none;
                            font-weight:bold;
                            font-size:18px;
                            margin-top:10px;
                        ">
                            🏨 Book on Booking.com
                        </a>
                        """,
                        unsafe_allow_html=True
                    )

                with col2:
                    st.markdown(
                        f"""
                        <a href="https://maps.google.com/?q={hotel_name}+{city_name}" target="_blank" style="
                            display:block;
                            text-align:center;
                            background-color:#ffa421 !important;
                            color:yellow !important;
                            padding:14px;
                            border-radius:12px;
                            text-decoration:none;
                            font-weight:bold;
                            font-size:18px;
                            margin-top:10px;
                        ">
                            📍 View on Maps
                        </a>
                        """,
                        unsafe_allow_html=True
                    )

            # Step 5: Weather Visualization
            if agents.weather_agent.LAST_FETCHED_WEATHER:
                weather_data = agents.weather_agent.LAST_FETCHED_WEATHER
                city = weather_data["city"]
                forecast = weather_data["forecast"]
                daily_data = forecast.get("daily", [])
                hourly_data = forecast.get("hourly", {})
                
                if daily_data:
                    st.subheader(f"🌤️ Weather Forecast for {city.title()}")
                    
                    # Create a tab for each day
                    tab_titles = [datetime.datetime.strptime(day["date"], "%Y-%m-%d").strftime("%b %d") for day in daily_data]
                    tabs = st.tabs(tab_titles)
                    
                    for idx, tab in enumerate(tabs):
                        day_info = daily_data[idx]
                        day_date_str = day_info["date"]
                        
                        with tab:
                            # Daily Summary Card
                            st.markdown(f"""
                            <div class="daily-summary">
                                <div class="daily-info">
                                    <h3>{datetime.datetime.strptime(day_date_str, "%Y-%m-%d").strftime("%A, %B %d")}</h3>
                                    <p>Max: {day_info['max_temp_celsius']}°C | Min: {day_info['min_temp_celsius']}°C</p>
                                </div>
                                <div class="daily-stats">
                                    <div class="stat-box">
                                        <div class="stat-val">{day_info['rain_probability_percent']}%</div>
                                        <div class="stat-label">Rain Prob</div>
                                    </div>
                                </div>
                                <div class="daily-emoji">{day_info['emoji']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Hourly Forecast Scroller
                            if day_date_str in hourly_data:
                                st.markdown("#### Hourly Forecast")
                                hours = hourly_data[day_date_str]
                                
                                hourly_html = '<div class="hourly-scroller">'
                                for hour in hours:
                                    time_obj = datetime.datetime.strptime(hour["time"], "%H:%M")
                                    time_formatted = time_obj.strftime("%I %p")
                                    
                                    hourly_html += f"""
<div class="hourly-card">
    <div class="hourly-time">{time_formatted}</div>
    <div class="hourly-emoji">{hour['emoji']}</div>
    <div class="hourly-temp">{hour['temp_celsius']}°C</div>
    <div class="hourly-rain">{hour['rain_probability_percent']}% Rain</div>
</div>
"""
                                hourly_html += '</div>'
                                
                                st.markdown(hourly_html, unsafe_allow_html=True)


            # Step 6: Google Maps Sections
            if valid_results:
                st.subheader("🗺️ Maps")
                for result in valid_results:
                    place = result["place"]
                    st.markdown(f"### 📍 {place}")
                    place_encoded = place.replace(" ", "+")
                    st.iframe(
                        f"https://maps.google.com/maps?q={place_encoded}&t=&z=13&ie=UTF8&iwloc=&output=embed",
                        height=300
                    )

        save_chat(active_query, response)
        st.session_state.messages.append({"role": "assistant", "content": response})