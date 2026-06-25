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
from agents.image_agent import fetch_destination_image, fetch_food_images
from agents.hotel_agent import fetch_hotel_info
from agents.restaurant_agent import fetch_restaurants

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

[data-testid="stChatMessage"] {
    border-radius:20px;
    padding:15px;
    margin-bottom:10px;
    box-shadow:0 4px 15px rgba(0,0,0,0.08);
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

/* TripAdvisor Hotel Card */
.ta-hotel-card {
    background: white;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.ta-featured-img {
    width: 100%;
    height: 300px;
    object-fit: cover;
}
.ta-hotel-body {
    padding: 24px;
}
.ta-hotel-name {
    font-size: 28px;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 8px 0;
}
.ta-hotel-ranking {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 16px;
}
.ta-award-badge {
    display: inline-block;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    color: #78350f;
    font-size: 13px;
    font-weight: 700;
    padding: 5px 14px;
    border-radius: 20px;
    margin-bottom: 16px;
}
.ta-metrics {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.ta-metric {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 20px;
    text-align: center;
    min-width: 100px;
}
.ta-metric-val {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
}
.ta-metric-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 600;
}
.ta-description {
    font-size: 15px;
    color: #334155;
    line-height: 1.7;
    margin-bottom: 20px;
}
.ta-contact {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 20px;
}
.ta-contact-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    color: #475569;
    background: #f1f5f9;
    padding: 8px 14px;
    border-radius: 8px;
}
.ta-price-range {
    display: inline-block;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    font-weight: 700;
    font-size: 15px;
    padding: 8px 18px;
    border-radius: 10px;
    margin-bottom: 20px;
}

/* Hotel Image Gallery */
.ta-gallery {
    display: flex;
    overflow-x: auto;
    gap: 12px;
    padding: 10px 0;
    scroll-behavior: smooth;
}
.ta-gallery::-webkit-scrollbar {
    height: 6px;
}
.ta-gallery::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;
}
.ta-gallery-img {
    flex: 0 0 auto;
    width: 220px;
    height: 160px;
    object-fit: cover;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* AI Review Summary */
.ta-ai-summary {
    background: linear-gradient(135deg, #eff6ff, #dbeafe);
    border: 1px solid #bfdbfe;
    border-radius: 14px;
    padding: 20px;
    margin: 16px 0;
}
.ta-ai-title {
    font-size: 16px;
    font-weight: 700;
    color: #1e40af;
    margin-bottom: 10px;
}
.ta-ai-text {
    font-size: 14px;
    color: #1e3a5f;
    line-height: 1.6;
}
.ta-attr-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 14px;
}
.ta-attr-chip {
    background: white;
    border: 1px solid #93c5fd;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
}
.ta-attr-name {
    font-weight: 700;
    color: #1e40af;
}
.ta-attr-opinion {
    color: #475569;
}

/* Booking Offers */
.ta-offers {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 16px 0;
}
.ta-offer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px 18px;
}
.ta-offer-provider {
    font-weight: 700;
    color: #0f172a;
    font-size: 15px;
}
.ta-offer-price {
    font-size: 20px;
    font-weight: 800;
    color: #059669;
}
.ta-offer-original {
    font-size: 13px;
    color: #94a3b8;
    text-decoration: line-through;
    margin-right: 6px;
}
.ta-offer-benefits {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 4px;
}
.ta-benefit-tag {
    font-size: 11px;
    background: #ecfdf5;
    color: #065f46;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 600;
}
.ta-lowest-tag {
    font-size: 11px;
    background: #fef3c7;
    color: #92400e;
    padding: 3px 8px;
    border-radius: 6px;
    font-weight: 700;
}
.ta-offer-link {
    display: inline-block;
    background: #3b82f6;
    color: white !important;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 13px;
}
.ta-offer-link:hover {
    background: #2563eb;
}

/* Rating Distribution */
.ta-rating-dist {
    margin: 16px 0;
}
.ta-rating-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
}
.ta-rating-label {
    font-size: 14px;
    font-weight: 600;
    color: #475569;
    width: 20px;
    text-align: right;
}
.ta-rating-bar-bg {
    flex: 1;
    height: 10px;
    background: #e2e8f0;
    border-radius: 5px;
    overflow: hidden;
}
.ta-rating-bar {
    height: 100%;
    background: linear-gradient(90deg, #fbbf24, #f59e0b);
    border-radius: 5px;
}
.ta-rating-count {
    font-size: 13px;
    color: #64748b;
    width: 50px;
}

/* Room Tips */
.ta-tip {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.ta-tip-text {
    font-size: 14px;
    color: #78350f;
    line-height: 1.5;
}
.ta-tip-user {
    font-size: 12px;
    color: #92400e;
    margin-top: 6px;
    font-weight: 600;
}

/* Restaurant Cards */
.rest-grid {
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin: 16px 0;
}
.rest-card {
    background: white;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: row;
}
.rest-card-img {
    width: 240px;
    min-height: 180px;
    object-fit: cover;
    flex-shrink: 0;
}
.rest-card-body {
    padding: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    flex: 1;
}
.rest-card-name {
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 6px 0;
}
.rest-card-location {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 12px;
}
.rest-card-links {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}
.rest-link-btn {
    display: inline-block;
    padding: 8px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 13px;
}
.rest-link-ta {
    background: #059669;
    color: white !important;
}
.rest-link-ta:hover {
    background: #047857;
}
.rest-link-map {
    background: #3b82f6;
    color: white !important;
}
.rest-link-map:hover {
    background: #2563eb;
}
@media (max-width: 640px) {
    .rest-card {
        flex-direction: column;
    }
    .rest-card-img {
        width: 100%;
        height: 200px;
    }
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
        Developed by <b><a href="https://www.linkedin.com/in/sayam-pradhan/" target="_blank">
            Sayam
        </a></b><br>
        Under the supervision of Prof. <b><a href="https://www.nitrkl.ac.in/CS/~deyp/" target="_blank">
            Prasenjit Dey
        </a></b><br>
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
    currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP", "AUD", "CAD", "SGD", "AED"])

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
        Further preferences to ask: {further_preferences},
        Currency: {currency}

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
            "travel_type": travelers,
            "currency": currency
        }
        st.rerun()


def _render_tripadvisor_section(hotel):
    """Render a rich TripAdvisor hotel details card."""
    st.subheader("🏨 Accommodation Details")

    # Featured image
    featured = hotel.get("featured_image")
    if featured:
        st.markdown(f'<img src="{featured}" class="ta-featured-img">', unsafe_allow_html=True)

    # Hotel name
    name = hotel.get("name", "Hotel")
    st.markdown(f'<div class="ta-hotel-body">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="ta-hotel-name">{name}</h2>', unsafe_allow_html=True)

    # Ranking
    ranking = hotel.get("ranking")
    if ranking:
        st.markdown(f'<div class="ta-hotel-ranking">{ranking.get("text", "")}</div>', unsafe_allow_html=True)

    # Award badge
    award = hotel.get("award")
    if award:
        st.markdown(f'<div class="ta-award-badge">🏆 {award.get("award_name", "")} {award.get("year", "")}</div>', unsafe_allow_html=True)

    # Metrics row: Rating, Reviews, Hotel Class, Rooms
    metrics_html = '<div class="ta-metrics">'
    if hotel.get("rating"):
        metrics_html += f'<div class="ta-metric"><div class="ta-metric-val">⭐ {hotel["rating"]}</div><div class="ta-metric-label">Rating</div></div>'
    if hotel.get("reviews"):
        metrics_html += f'<div class="ta-metric"><div class="ta-metric-val">{hotel["reviews"]:,}</div><div class="ta-metric-label">Reviews</div></div>'
    if hotel.get("hotel_class"):
        stars = "⭐" * int(hotel["hotel_class"])
        metrics_html += f'<div class="ta-metric"><div class="ta-metric-val">{stars}</div><div class="ta-metric-label">{hotel["hotel_class"]}-Star Hotel</div></div>'
    if hotel.get("number_of_rooms"):
        metrics_html += f'<div class="ta-metric"><div class="ta-metric-val">{hotel["number_of_rooms"]}</div><div class="ta-metric-label">Rooms</div></div>'
    metrics_html += '</div>'
    st.markdown(metrics_html, unsafe_allow_html=True)

    # Price range
    price_range = hotel.get("price_range")
    if price_range and price_range.get("minimum") and price_range.get("maximum"):
        currency = price_range.get("currency", "INR")
        st.markdown(f'<div class="ta-price-range">💰 {currency} {price_range["minimum"]} – {price_range["maximum"]} per night</div>', unsafe_allow_html=True)

    # Description
    desc = hotel.get("description")
    if desc:
        st.markdown(f'<div class="ta-description">{desc}</div>', unsafe_allow_html=True)

    # Contact info
    contact_html = '<div class="ta-contact">'
    if hotel.get("address"):
        contact_html += f'<div class="ta-contact-item">📍 {hotel["address"]}</div>'
    if hotel.get("phone"):
        contact_html += f'<div class="ta-contact-item">📞 {hotel["phone"]}</div>'
    if hotel.get("email"):
        contact_html += f'<div class="ta-contact-item">📧 {hotel["email"]}</div>'
    if hotel.get("website"):
        contact_html += f'<div class="ta-contact-item"><a href="{hotel["website"]}" target="_blank" style="color:#3b82f6;text-decoration:none;">🌐 Official Website</a></div>'
    if hotel.get("link"):
        contact_html += f'<div class="ta-contact-item"><a href="{hotel["link"]}" target="_blank" style="color:#3b82f6;text-decoration:none;">📄 TripAdvisor Page</a></div>'
    contact_html += '</div>'
    st.markdown(contact_html, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Image gallery
    images = hotel.get("images", [])
    if images:
        st.markdown("#### 📸 Hotel Gallery")
        gallery_html = '<div class="ta-gallery">'
        for img in images[:15]:  # Show up to 15 images
            img_link = img.get("image_link", "")
            caption = img.get("caption", "")
            if img_link:
                gallery_html += f'<img src="{img_link}" class="ta-gallery-img" title="{caption or ""}" alt="{caption or ""}" />'
        gallery_html += '</div>'
        st.markdown(gallery_html, unsafe_allow_html=True)

    # AI Review Summary
    ai_summary = hotel.get("ai_review_summary")
    if ai_summary:
        summary_html = '<div class="ta-ai-summary">'
        summary_html += '<div class="ta-ai-title">🤖 AI Review Summary</div>'
        summary_html += f'<div class="ta-ai-text">{ai_summary.get("summary_text", "")}</div>'
        attrs = ai_summary.get("attribute_summaries", [])
        if attrs:
            summary_html += '<div class="ta-attr-grid">'
            for attr in attrs:
                summary_html += f'<div class="ta-attr-chip"><span class="ta-attr-name">{attr.get("attribute", "")}:</span> <span class="ta-attr-opinion">{attr.get("opinion", "")}</span></div>'
            summary_html += '</div>'
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

    # Rating Distribution
    rating_dist = hotel.get("rating_distribution")
    if rating_dist:
        st.markdown("#### 📊 Rating Distribution")
        total_reviews = sum(int(v) for v in rating_dist.values())
        dist_html = '<div class="ta-rating-dist">'
        for star in ["5", "4", "3", "2", "1"]:
            count = int(rating_dist.get(star, 0))
            pct = (count / total_reviews * 100) if total_reviews > 0 else 0
            dist_html += f'''<div class="ta-rating-row">
                <div class="ta-rating-label">{star}★</div>
                <div class="ta-rating-bar-bg"><div class="ta-rating-bar" style="width:{pct:.1f}%"></div></div>
                <div class="ta-rating-count">{count:,}</div>
            </div>'''
        dist_html += '</div>'
        st.markdown(dist_html, unsafe_allow_html=True)

    # Booking Offers (top 3 from booking_offers)
    offers = hotel.get("booking_offers", [])
    more_offers = hotel.get("more_booking_offers", [])
    all_offers = offers + more_offers
    available_offers = [o for o in all_offers if o.get("is_available") and o.get("price", {}).get("amount")]
    available_offers.sort(key=lambda o: o["price"]["amount"])

    if available_offers:
        st.markdown("#### 💳 Booking Options (Sorted by Price)")
        offers_html = '<div class="ta-offers">'
        for offer in available_offers[:6]:  # Show top 6
            price = offer["price"]
            provider = offer.get("provider_name", "")
            amount = price.get("text", "")
            original = price.get("original_text", "")
            is_lowest = offer.get("is_lowest_price", False)
            link = offer.get("booking_link", "")
            benefits = offer.get("benefits", [])
            rooms_left = offer.get("rooms_remaining")

            offers_html += '<div class="ta-offer">'
            offers_html += '<div>'
            offers_html += f'<div class="ta-offer-provider">{provider}</div>'

            benefit_html = '<div class="ta-offer-benefits">'
            if is_lowest:
                benefit_html += '<span class="ta-lowest-tag">⚡ Lowest Price</span>'
            for b in benefits:
                benefit_html += f'<span class="ta-benefit-tag">{b.get("text", "")}</span>'
            if rooms_left and rooms_left < 10:
                benefit_html += f'<span class="ta-benefit-tag">🔥 Only {rooms_left} left!</span>'
            benefit_html += '</div>'
            offers_html += benefit_html

            offers_html += '</div>'
            offers_html += '<div style="text-align:right;">'
            if original:
                offers_html += f'<span class="ta-offer-original">{original}</span>'
            offers_html += f'<div class="ta-offer-price">{amount}</div>'
            if link:
                offers_html += f'<a href="{link}" target="_blank" class="ta-offer-link">Book Now →</a>'
            offers_html += '</div>'
            offers_html += '</div>'
        offers_html += '</div>'
        st.markdown(offers_html, unsafe_allow_html=True)

    # Room Tips (top 3)
    room_tips = hotel.get("room_tips", [])
    if room_tips:
        st.markdown("#### 💡 Guest Tips")
        for tip in room_tips[:3]:
            tip_text = tip.get("tip_text", "")
            tip_user = tip.get("user", {}).get("name", "")
            tip_rating = tip.get("rating", 0)
            stars = "⭐" * tip_rating
            st.markdown(f'''<div class="ta-tip">
                <div class="ta-tip-text">"{tip_text}"</div>
                <div class="ta-tip-user">— {tip_user} {stars}</div>
            </div>''', unsafe_allow_html=True)

    st.markdown("---")


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
    
    # TripAdvisor hotel details (shown before booking buttons)
    if message.get("tripadvisor_data"):
        _render_tripadvisor_section(message["tripadvisor_data"])

    # Booking buttons
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

    # Restaurants section
    if message.get("restaurants_data"):
        _render_restaurants_section(message["restaurants_data"])

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


def _render_restaurants_section(restaurants):
    """Render a list of restaurant cards with images and embedded maps."""
    if not restaurants:
        return

    st.subheader("🍽️ Recommended Restaurants")

    for rest in restaurants:
        name = rest.get("name", "")
        image = rest.get("featured_image", "")
        link = rest.get("link", "")
        location = rest.get("parent_location", "")
        coords = rest.get("coordinates", {})
        lat = coords.get("latitude")
        lon = coords.get("longitude")

        # Restaurant card with image
        card_html = '<div class="rest-card">'
        if image:
            card_html += f'<img src="{image}" class="rest-card-img" alt="{name}" />'
        card_html += '<div class="rest-card-body">'
        card_html += f'<div class="rest-card-name">{name}</div>'
        if location:
            card_html += f'<div class="rest-card-location">📍 {location}</div>'
        card_html += '<div class="rest-card-links">'
        if link:
            card_html += f'<a href="{link}" target="_blank" class="rest-link-btn rest-link-ta">View on TripAdvisor</a>'
        if lat and lon:
            map_url = f"https://maps.google.com/?q={lat},{lon}"
            card_html += f'<a href="{map_url}" target="_blank" class="rest-link-btn rest-link-map">Open in Maps</a>'
        card_html += '</div></div></div>'
        st.markdown(card_html, unsafe_allow_html=True)

        # Embedded Google Map
        if lat and lon:
            map_query = f"{name}+{location}".replace(" ", "+")
            st.iframe(
                f"https://maps.google.com/maps?q={map_query}&t=&z=15&ie=UTF8&iwloc=&output=embed",
                height=250
            )

    st.markdown("---")


# -------------------------------------------------
# Session State & Main Chat

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            render_rich_message(message)
        else:
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
        st.error("API Key not found! Please check your .env file configuration.")
    else:
        with st.chat_message("assistant"):
            # Step 1: Agent Generation
            with st.spinner("Thinking..."):
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

            is_trip_plan = names.get("is_trip_plan", False)
            valid_results = []
            msg_data = {"role": "assistant", "content": response}

            # Step 2: Destination Images
            if is_trip_plan:
                with st.spinner("Loading destination gallery..."):
                    with ThreadPoolExecutor(max_workers=8) as executor:
                        results = list(executor.map(fetch_destination_image, names.get("destinations", [])))
                        food_results = list(executor.map(fetch_food_images, names.get("foods", [])))
                    valid_results = [r for r in results if r]
                    valid_food_results = [r for r in food_results if r]


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

                    # Fetch TripAdvisor details
                    with st.spinner("Loading hotel details from TripAdvisor..."):
                        try:
                            currency_param = trip_params.get("currency", "INR") if trip_params else "INR"
                            ta_data = fetch_hotel_info(hotel_name, city_name, currency=currency_param)
                            if ta_data:
                                msg_data["tripadvisor_data"] = ta_data
                                logger.info(f"TripAdvisor data fetched for {hotel_name}")
                        except Exception as e:
                            logger.error(f"Failed to fetch TripAdvisor data: {e}")

                # Fetch restaurant details
                restaurant_names = names.get("restaurants", []) if is_trip_plan else []
                if restaurant_names:
                    with st.spinner("Loading restaurant details..."):
                        try:
                            rest_data = fetch_restaurants(restaurant_names, currency_param)
                            if rest_data:
                                msg_data["restaurants_data"] = rest_data
                                logger.info(f"Fetched {len(rest_data)} restaurants from TripAdvisor")
                        except Exception as e:
                            logger.error(f"Failed to fetch restaurant data: {e}")

                if is_trip_plan and agents.weather_agent.LAST_FETCHED_WEATHER:
                    msg_data["weather"] = agents.weather_agent.LAST_FETCHED_WEATHER

                if valid_results:
                    msg_data["maps"] = [r["place"].replace(" ", "+") for r in valid_results]

                render_rich_message(msg_data)
            else:
                render_rich_message(msg_data)

        save_chat(active_query, response)
        st.session_state.messages.append(msg_data)