import streamlit as st
import uuid
import matplotlib.pyplot as plt
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# --- CUSTOM MODULES ---
from guru_db import init_db, save_message, load_history, clear_session, get_all_sessions, save_setting, load_setting, \
    get_user_plan
from themes import THEMES, inject_theme_css
from guru_engine import DataEngine
from guru_brain import build_agent_graph, get_key_status

# --- SECURITY & REPORTING MODULES ---
from guru_security import check_password, logout
from guru_report import generate_pdf

# --- UI CONFIG ---
st.set_page_config(page_title="Ask-GuruAi", layout="wide", page_icon="💡")

# --- 1. SECURITY GATE (Login Screen) ---
if not check_password():
    st.stop()

init_db()

# --- INITIALIZE STATE ---
if "data_engine" not in st.session_state: st.session_state.data_engine = DataEngine()
engine = st.session_state.data_engine

# --- MULTI-USER SESSION MANAGEMENT ---
current_user = st.session_state.get("username", "guest")

# [NEW] Load User Plan
if "user_plan" not in st.session_state:
    st.session_state.user_plan = get_user_plan(current_user)
user_plan = st.session_state.user_plan

# Prefix session ID with username
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = f"{current_user}-Session-{uuid.uuid4().hex[:4]}"

if not st.session_state.current_session_id.startswith(f"{current_user}-"):
    st.session_state.current_session_id = f"{current_user}-Session-{uuid.uuid4().hex[:4]}"

current_sess = st.session_state.current_session_id

# --- BUILD BRAIN ---
app = build_agent_graph(engine)

# --- SIDEBAR & THEME ---
current_theme = load_setting("theme", "GuruAi Enterprise")
inject_theme_css(current_theme)
theme_data = THEMES.get(current_theme, THEMES["GuruAi Enterprise"])

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚡ GURU HQ")
    st.write(f"👤 **User:** {current_user}")
    st.caption(get_key_status())

    # REMOVED: Plan Status Indicator and Upgrade Button

    if st.button("🔒 Logout", use_container_width=True):
        logout()

    st.divider()

    # --- DATA CENTER ---
    st.markdown("### 📂 Data Center")

    # SIMPLIFIED: All users get all file types
    allowed_types = ['csv', 'xlsx', 'xls', 'json', 'pdf', 'docx']
    uploaded_file = st.file_uploader("Upload Dataset", type=allowed_types)

    # SIMPLIFIED: Google Sheet enabled for everyone
    gsheet_url = st.text_input("🔗 Google Sheet URL")
    if gsheet_url and st.button("Load Sheet"):
        st.info(f"Loading Sheet: {gsheet_url}...")

    if uploaded_file:
        status = engine.load_file(uploaded_file)
        if "Error" in status:
            st.error(status)
        else:
            st.success(status)

    if st.button("🧹 Clear Plots", use_container_width=True):
        plt.clf()
        engine.latest_figure = None
        if os.path.exists("temp_chart.png"): os.remove("temp_chart.png")
        st.success("Plots cleared.")

    st.divider()

    # --- 3. REPORTING ---
    st.markdown("### 📄 Reporting")
    if st.button("📥 Export PDF Report", use_container_width=True):
        with st.spinner("Compiling PDF..."):
            history = load_history(current_sess)
            pdf_file = generate_pdf(history, current_sess)
        with open(pdf_file, "rb") as f:
            st.download_button("⬇️ Download PDF", f, file_name=pdf_file, use_container_width=True)

    st.divider()

    st.markdown("### 🕒 Session History")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ New", use_container_width=True):
            st.session_state.current_session_id = f"{current_user}-Session-{uuid.uuid4().hex[:4]}"
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            clear_session(current_sess)
            st.rerun()

    # List recent sessions
    st.caption("Recent Sessions:")
    my_sessions = [s for s in get_all_sessions() if s.startswith(f"{current_user}-")]

    for s in my_sessions[:5]:
        display_name = s.replace(f"{current_user}-", "")
        if st.button(f"📂 {display_name}", key=s, use_container_width=True):
            st.session_state.current_session_id = s
            st.rerun()

# --- CHAT INTERFACE ---
st.title("GuruAi Intelligent Analytics")

# Load History
history = load_history(current_sess)
for msg in history:
    role = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(role, avatar=theme_data["user_avatar"] if role == "user" else theme_data["ai_avatar"]):
        st.markdown(msg["content"])

# --- INPUT HANDLING ---
prompt = st.chat_input("Enter analysis command...")

if prompt:
    # 1. UI Echo
    with st.chat_message("user", avatar=theme_data["user_avatar"]):
        st.markdown(prompt)
    save_message(current_sess, "user", prompt)

    # 2. Refresh Context
    if engine.df is not None and not engine.column_str:
        engine.column_str = ", ".join(list(engine.df.columns))

    # 3. Construct System Prompt (Simplified)
    system_text = "You are GuruAi, a professional data analyst. Use 'python_analysis' for data tasks."

    if engine.df is not None:
        system_text += f"\n[DATA ACTIVE] Columns: {engine.column_str}. ALWAYS use print() to show table outputs."

    # 4. Context Window
    recent_history = history[-2:]

    messages = [SystemMessage(content=system_text)] + \
               [HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]) for m in
                recent_history] + \
               [HumanMessage(content=prompt)]

    # 5. Run Agent
    with st.chat_message("assistant", avatar=theme_data["ai_avatar"]):
        status_box = st.status("Thinking...", expanded=True)
        try:
            final_resp = ""
            # Stream the graph events
            for event in app.stream({"messages": messages}, config={"recursion_limit": 60}, stream_mode="values"):
                msg = event["messages"][-1]

                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for t in msg.tool_calls:
                        status_box.write(f"⚙️ Action: `{t['name']}`")

                if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                    final_resp = msg.content

            # A. Render Chart (if generated)
            if engine.latest_figure:
                st.pyplot(engine.latest_figure)
                chart_path = f"chart_{current_sess}.png"
                engine.latest_figure.savefig(chart_path)
                engine.latest_figure = None

            # B. Render Text Response
            if final_resp:
                st.markdown(final_resp)
                status_box.update(label="Complete", state="complete", expanded=False)
                save_message(current_sess, "assistant", final_resp)
            else:
                status_box.update(label="Task Completed", state="complete", expanded=False)

        except Exception as e:
            status_box.update(label="Error", state="error")
            st.error(f"Error: {e}")