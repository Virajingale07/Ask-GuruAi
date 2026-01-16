import streamlit as st
from supabase import create_client, Client


# --- CONNECTION MANAGER ---
@st.cache_resource
def get_supabase_client() -> Client:
    """
    Establishes a connection to Supabase using secrets.
    Includes validation to catch httpx.ConnectError triggers early.
    """
    try:
        # 1. Fetch credentials from Streamlit Secrets
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")

        # 2. Validate URL presence and format to prevent connection failures
        if not url or not key:
            st.error("🔑 Missing Supabase credentials in Streamlit Secrets.")
            st.stop()

        if not url.startswith("https://"):
            st.error("🌐 Invalid SUPABASE_URL format. It must start with 'https://'.")
            st.stop()

        # 3. Initialize client
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Database Connection Failed: {e}")
        st.info("Check if your Supabase project is paused or if the URL is copied correctly.")
        st.stop()


def init_db():
    """Verifies database connection and table existence on startup."""
    try:
        client = get_supabase_client()
        # Verify 'chat_history' table is accessible
        client.table("chat_history").select("id", count="exact").limit(1).execute()
    except Exception as e:
        st.warning(f"⚠️ Database Table Warning: {e}. Ensure tables 'users' and 'chat_history' exist.")


# --- CHAT HISTORY FUNCTIONS ---

def save_message(session_id, role, content):
    """Saves a message to Supabase with the current username."""
    client = get_supabase_client()
    username = st.session_state.get("username", "guest")

    data = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "username": username
    }
    client.table("chat_history").insert(data).execute()


def load_history(session_id):
    """Loads chat history for a specific session."""
    client = get_supabase_client()
    response = client.table("chat_history") \
        .select("*") \
        .eq("session_id", session_id) \
        .order("created_at", desc=False) \
        .execute()
    return response.data


def clear_session(session_id):
    """Deletes all messages for a specific session."""
    client = get_supabase_client()
    client.table("chat_history").delete().eq("session_id", session_id).execute()


def get_all_sessions():
    """Retrieves unique session IDs for the logged-in user."""
    client = get_supabase_client()
    username = st.session_state.get("username", "guest")

    response = client.table("chat_history") \
        .select("session_id") \
        .eq("username", username) \
        .order("created_at", desc=True) \
        .execute()

    unique_sessions = []
    seen = set()
    for row in response.data:
        sid = row['session_id']
        if sid not in seen:
            unique_sessions.append(sid)
            seen.add(sid)

    return unique_sessions


# --- SETTINGS MANAGEMENT ---

def save_setting(key, value):
    """Saves app settings to the session state."""
    st.session_state[f"setting_{key}"] = value


def load_setting(key, default):
    """Loads app settings from the session state."""
    return st.session_state.get(f"setting_{key}", default)