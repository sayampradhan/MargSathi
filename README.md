# MargSathi Chatbot

MargSathi is an intelligent travel planning assistant developed using Streamlit and Gemini API. It handles destination planning, hotel booking suggestions, weather forecasting, dynamic image fetching via Wikimedia Commons, and rich hotel and restaurant details via the TripAdvisor API.

## Project Structure

```text
chatbot/
├── .env                  # Environment variables (API Keys)
├── config.py             # Configuration and settings loader
├── main.py               # Streamlit application entry point
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
├── agents/               # AI and Logic Agents
│   ├── hotel_agent.py    # Fetches rich hotel details from TripAdvisor
│   ├── image_agent.py    # Fetches images directly from Wikimedia Commons
│   ├── travel_guide.py   # Handles interaction with Gemini for travel plans
│   └── weather_agent.py  # Fetches weather forecasts via Open-Meteo API
├── database/             # Supabase/PostgreSQL Caching Layer
│   ├── database.py       # SQLAlchemy engine and session management
│   ├── models/           # SQLAlchemy ORM models (ImageCache, TripCache, etc.)
│   └── repositories/     # Database operation wrappers (ImageRepository, TripRepository, etc.)
├── supabase/             # Supabase configuration for local development
└── utils/                # Helper utilities
    └── helpers.py        # Generic utilities like JSON extraction, LLM fallbacks (Groq), and URL builders
```

## Setup & Installation

1. **Install Dependencies:**
   Ensure you have Python installed. You will need the following libraries:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add the necessary API keys and database URL.
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   TRIPADVISOR_API_KEY=your_tripadvisor_api_key_here
   DATABASE_URL=your_postgresql_database_url_here
   ```

3. **Run the Application:**
   Start the Streamlit application by running:
   ```bash
   streamlit run main.py
   ```

## Architecture Notes

*   **Clean Architecture:** Business logic is separated into `agents/`, generic functions into `utils/`, UI into `main.py`, and persistent state into `database/`.
*   **Database Caching:** Uses SQLAlchemy and PostgreSQL (via Supabase) to cache API responses (trips, images, weather forecasts), dramatically improving performance and reducing external API calls.
*   **No LLM Dependency for Images:** The image agent directly queries Wikimedia Commons and retrieves images based on search relevance, reducing LLM token usage and latency.
*   **Automatic Fallbacks:** Incorporates automatic LLM failovers (e.g., from Gemini to Groq for structured extraction) to ensure the system is highly resilient and responsive.
*   **Environment Configuration:** Sensitive information is managed via `.env` to prevent accidental exposure of API keys.
