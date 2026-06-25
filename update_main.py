import os

# Read main.py
with open("main.py", "r") as f:
    content = f.read()

# Define the helper function
helper_func = """
def render_rich_message(message):
    if message.get("destinations_html"):
        st.subheader("📍 Destinations")
        st.html(message["destinations_html"])
        st.markdown("---")
        
    if message.get("foods_html"):
        st.subheader("🍜 Local Foods")
        st.html(message["foods_html"])
        st.markdown("---")
        
    st.markdown(message.get("content", ""))
    
    if message.get("hotel_info"):
        h = message["hotel_info"]
        st.subheader("🛏️ Book Hotel")
        st.write(f"**Hotel:** {h['name']}")
        st.write(f"**City:** {h['city']}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'''
                <a href="{h['url']}" target="_blank" style="
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
                ''',
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f'''
                <a href="https://maps.google.com/?q={h['name']}+{h['city']}" target="_blank" style="
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
                ''',
                unsafe_allow_html=True
            )

    if message.get("weather"):
        weather_data = message["weather"]
        city = weather_data["city"]
        forecast = weather_data["forecast"]
        daily_data = forecast.get("daily", [])
        hourly_data = forecast.get("hourly", {})
        
        if daily_data:
            st.subheader(f"🌤️ Weather Forecast for {city.title()}")
            
            tab_titles = [datetime.datetime.strptime(day["date"], "%Y-%m-%d").strftime("%b %d") for day in daily_data]
            tabs = st.tabs(tab_titles)
            
            for idx, tab in enumerate(tabs):
                day_info = daily_data[idx]
                day_date_str = day_info["date"]
                
                with tab:
                    st.markdown(f'''
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
                    ''', unsafe_allow_html=True)
                    
                    if day_date_str in hourly_data:
                        st.markdown("#### Hourly Forecast")
                        hours = hourly_data[day_date_str]
                        
                        hourly_html = '<div class="hourly-scroller">'
                        for hour in hours:
                            time_obj = datetime.datetime.strptime(hour["time"], "%H:%M")
                            time_formatted = time_obj.strftime("%I %p")
                            
                            hourly_html += f'''
<div class="hourly-card">
    <div class="hourly-time">{time_formatted}</div>
    <div class="hourly-emoji">{hour['emoji']}</div>
    <div class="hourly-temp">{hour['temp_celsius']}°C</div>
    <div class="hourly-rain">{hour['rain_probability_percent']}% Rain</div>
</div>
'''
                        hourly_html += '</div>'
                        st.markdown(hourly_html, unsafe_allow_html=True)

    if message.get("maps"):
        st.subheader("🗺️ Maps")
        for place_encoded in message["maps"]:
            place_dec = place_encoded.replace("+", " ")
            st.markdown(f"### 📍 {place_dec}")
            st.iframe(
                f"https://maps.google.com/maps?q={place_encoded}&t=&z=13&ie=UTF8&iwloc=&output=embed",
                height=300
            )

# -------------------------------------------------
# Session State & Main Chat
"""

# Replace the start of session state section to inject helper
content = content.replace(
    "# -------------------------------------------------\n# Session State & Main Chat\n# -------------------------------------------------",
    helper_func
)

# Update the rendering loop to use the helper function
old_loop = """for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])"""

new_loop = """for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_rich_message(message)
        else:
            st.markdown(message["content"])"""

content = content.replace(old_loop, new_loop)

# Reconstruct the active query generation part
# We find where valid_food_results is finalized
split_target = "                    valid_food_results = [r for r in food_results if r]"
parts = content.split(split_target)

# We want to replace everything after this split target up to save_chat
if len(parts) == 2:
    end_split = "        save_chat(active_query, response)"
    after_parts = parts[1].split(end_split)
    
    if len(after_parts) == 2:
        new_block = """
                msg_data = {"role": "assistant", "content": response}

                if valid_results:
                    gallery_html = '''
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
                    '''
                    for result in valid_results:
                        place = result["place"]
                        images = result.get("image", [])
                        if not images:
                            continue
                        img_url = images[0].get("url")
                        if not img_url:
                            continue
                        gallery_html += f'''
                        <div class="image-card">
                            <img src="{img_url}">
                            <div class="image-title">{place}</div>
                        </div>
                        '''
                    gallery_html += "</div>"
                    msg_data["destinations_html"] = gallery_html

                if valid_food_results:
                    food_gallery_html = '''
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
                    '''
                    for result in valid_food_results:
                        food = result["food"]
                        images = result.get("image", [])
                        if not images:
                            continue
                        img_url = images[0].get("url")
                        if not img_url:
                            continue
                        food_gallery_html += f'''
                        <div class="image-card">
                            <img src="{img_url}">
                            <div class="image-title">{food}</div>
                        </div>
                        '''
                    food_gallery_html += "</div>"
                    msg_data["foods_html"] = food_gallery_html

                hotel_names = names.get("hotel", []) if is_trip_plan else []
                hotel_cities = names.get("hotel_city", []) if is_trip_plan else []

                if hotel_names and hotel_cities:
                    hotel_name = hotel_names[0]
                    city_name = hotel_cities[0]
                    booking_url = hotel_booking(hotel_name, city_name)
                    msg_data["hotel_info"] = {"name": hotel_name, "city": city_name, "url": booking_url}

                if is_trip_plan and agents.weather_agent.LAST_FETCHED_WEATHER:
                    msg_data["weather"] = agents.weather_agent.LAST_FETCHED_WEATHER

                if valid_results:
                    msg_data["maps"] = [r["place"].replace(" ", "+") for r in valid_results]

                render_rich_message(msg_data)

"""
        
        # We also need to fix the append logic at the very end
        end_str = after_parts[1].replace(
            'st.session_state.messages.append({"role": "assistant", "content": response})',
            'st.session_state.messages.append(msg_data)'
        )
        
        final_content = parts[0] + split_target + new_block + end_split + end_str
        
        with open("main.py", "w") as f:
            f.write(final_content)
        print("Successfully updated main.py")
    else:
        print("Failed to split on save_chat")
else:
    print("Failed to split on valid_food_results")

