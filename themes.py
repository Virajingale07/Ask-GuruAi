import streamlit as st

# --- PROFESSIONAL THEME DEFINITION ---
THEMES = {
    "GuruAi Enterprise": {
        "primary": "#3B82F6",  # Professional Royal Blue
        "background": "#0E1117",  # Deep Charcoal (Standard Streamlit Dark)
        "sidebar": "#161B22",  # Slightly lighter dark for sidebar
        "text": "#F3F4F6",  # Off-white for readability
        "user_avatar": "🧑‍💼",  # Professional User Icon
        "ai_avatar": "⚡",  # Minimalist AI Icon
        "font": "sans-serif"
    }
}


def inject_theme_css(theme_name):
    """Injects professional Ask-GuruAi CSS styles into the app."""
    theme = THEMES.get(theme_name, THEMES["GuruAi Enterprise"])

    css = f"""
    <style>
        /* 1. GLOBAL STYLES */
        .stApp {{
            background-color: {theme['background']};
            font-family: 'Inter', -apple-system, sans-serif;
        }}

        /* 2. PREMIUM GRADIENT BUTTONS */
        div.stButton > button {{
            background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
            color: white !important;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-size: 14px;
        }}

        div.stButton > button:hover {{
            background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.3);
            transform: translateY(-2px);
            border: none;
        }}

        /* 3. DANGER BUTTON (Logout/Clear) */
        /* Targets buttons that should look like 'Danger' actions */
        div.stButton > button:contains("Logout"), 
        div.stButton > button:contains("Clear"),
        div.stButton > button:contains("🗑️") {{
            background: #1F2937;
            border: 1px solid #374151;
        }}

        div.stButton > button:contains("Logout"):hover {{
            background: #EF4444 !important;
            border: none;
        }}

        /* 4. SIDEBAR REFINEMENT */
        [data-testid="stSidebar"] {{
            background-color: {theme['sidebar']};
            border-right: 1px solid #30363D;
        }}

        [data-testid="stSidebarNav"] {{
            background-color: transparent;
        }}

        /* 5. DATA CENTER CARDS */
        .stAlert {{
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 10px;
        }}

        /* 6. CHAT INPUT FOCUS */
        .stChatInputContainer textarea {{
            border: 1px solid #30363D !important;
            focus-border-color: #3B82F6 !important;
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)