# MargSathi Chatbot

MargSathi is an intelligent travel planning assistant developed using Streamlit and Gemini API. It handles destination planning, hotel booking suggestions, weather forecasting, and dynamic image fetching via Wikimedia Commons.

## Project Structure

```text
chatbot/
├── .env                  # Environment variables (API Keys)
├── config.py             # Configuration and settings loader
├── main.py               # Streamlit application entry point
├── README.md             # Project documentation
├── agents/               # AI and Logic Agents
│   ├── image_agent.py    # Fetches images directly from Wikimedia Commons
│   ├── travel_guide.py   # Handles interaction with Gemini for travel plans
│   └── weather_agent.py  # Fetches weather forecasts via Open-Meteo API
└── utils/                # Helper utilities
    └── helpers.py        # Generic utilities like JSON extraction and URL builders
```

## Setup & Installation

1. **Install Dependencies:**
   Ensure you have Python installed. You will need the following libraries:
   ```bash
   pip install streamlit requests python-dotenv google-genai
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory (this should already exist if you followed the refactor setup) and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

3. **Run the Application:**
   Start the Streamlit application by running:
   ```bash
   streamlit run main.py
   ```

## Architecture Notes

*   **Clean Architecture:** Business logic is separated into `agents/`, generic functions into `utils/`, and UI into `main.py`.
*   **No LLM Dependency for Images:** The image agent directly queries Wikimedia Commons and retrieves images based on search relevance, reducing LLM token usage and latency.
*   **Environment Configuration:** Sensitive information is managed via `.env` to prevent accidental exposure of API keys.
