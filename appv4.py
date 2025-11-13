import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd
import json

# =========================
# Setup
# =========================
load_dotenv()

# Charlotte colors
CHARLOTTE_GREEN = "#005035"  # Charlotte Green
CHARLOTTE_GREEN_DARK = "#003D2A"  # Darker green for bubbles
NINER_GOLD = "#A49665"       # Niner Gold
QUARTZ_WHITE = "#FFFFFF"

st.set_page_config(
    page_title="CoursePath Chatbot – Charlotte",
    page_icon="🎓",
    layout="wide",
)

# =========================
# Custom UNC Charlotte-themed CSS
# =========================
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {QUARTZ_WHITE};
    }}

    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {CHARLOTTE_GREEN} 0%, #013222 100%);
        color: white;
    }}
    section[data-testid="stSidebar"] * {{
        color: white !important;
    }}

    /* Title styling */
    .unc-title {{
        color: {CHARLOTTE_GREEN};
        font-weight: 900;
        letter-spacing: 0.03em;
        font-size: 2.2rem;
    }}

    /* DARKER chat bubbles */

    .chat-user {{
        background-color: {CHARLOTTE_GREEN_DARK};
        border-left: 6px solid {NINER_GOLD};
        padding: 0.85rem 1rem;
        border-radius: 0.6rem;
        margin-bottom: 0.8rem;
        color: #FFFFFF !important;
    }}

    .chat-user strong {{
        color: #FFFFFF !important;
    }}

    .chat-assistant {{
        background-color: #243018;
        border-left: 6px solid {NINER_GOLD};
        padding: 0.85rem 1rem;
        border-radius: 0.6rem;
        margin-bottom: 0.8rem;
        color: #FFFFFF !important;
    }}

    .chat-assistant strong {{
        color: #FFFFFF !important;
    }}

    /* Welcome header */
    .unc-welcome {{
        color: {CHARLOTTE_GREEN_DARK};
        font-weight: 700;
        font-size: 1.6rem;
        margin-bottom: 1.2rem;
    }}

    /* Buttons */
    button[kind="secondary"], button[kind="primary"] {{
        border-radius: 999px !important;
        border: 1px solid {CHARLOTTE_GREEN} !important;
    }}
    button:hover {{
        box-shadow: 0 0 0 1px {NINER_GOLD}66;
    }}

    /* Text input / text area */
    textarea, input[type="text"] {{
        border-radius: 0.5rem !important;
        border: 1px solid {CHARLOTTE_GREEN}55 !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_NEW"))

USER_DATA_DIR = "user_data"
os.makedirs(USER_DATA_DIR, exist_ok=True)

@st.cache_data
def load_courses():
    return pd.read_csv("Courses.csv")  # Use your new dataset

df = load_courses()

# Build detailed course summary for GPT context
course_summary = "\n".join(
    (
        f"{row.course_id}: {row.course_name} "
        f"[{'Core' if bool(row.is_core) else 'Elective'}, {row.credits} credits]"
        f"{' - ' + row.concentration if pd.notna(row.concentration) else ''} | "
        f"Prerequisites: {row.prerequisites if pd.notna(row.prerequisites) else 'None'}"
    )
    for _, row in df.iterrows()
)

# Title with UNC Charlotte styling
st.markdown('<h1 class="unc-title">🎓 CoursePath Chatbot</h1>', unsafe_allow_html=True)
st.caption("Graduate CS advising with a Niner twist.")

# =========================
# Sidebar: Login / Test Mode
# =========================
st.sidebar.header("🔐 User Settings")
use_mock = st.sidebar.checkbox("Use Mock Mode (no API calls)", value=True)
st.sidebar.text(f"Using org: {client.organization}")

if "user" not in st.session_state:
    st.session_state.user = None

username = st.sidebar.text_input("Username")


def load_user_data(username):
    user_file = os.path.join(USER_DATA_DIR, f"{username}.json")
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            return json.load(f)
    else:
        return [
            {
                "role": "system",
                "content": (
                    "You are a helpful academic advisor for UNC Charlotte graduate "
                    "Computer Science students. Use this course catalog:\n"
                    f"{course_summary}\n"
                    "Recommend courses respecting prerequisites, concentrations, "
                    "core vs elective status, and typical semester loads."
                ),
            }
        ]


def save_user_data(username, data):
    user_file = os.path.join(USER_DATA_DIR, f"{username}.json")
    with open(user_file, "w") as f:
        json.dump(data, f, indent=2)


# Buttons
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("Login / Register"):
        if username:
            st.session_state.user = username
            st.session_state[f"{username}_messages"] = load_user_data(username)
            st.rerun()
        else:
            st.sidebar.error("Please enter a username.")

with col2:
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

# =========================
# Chat UI
# =========================
if st.session_state.user is None:
    st.info("👋 Please log in to start chatting.")
else:
    st.markdown(
        f'<p class="unc-welcome">Welcome, {st.session_state.user}! 👋</p>',
        unsafe_allow_html=True,
    )

    messages_key = f"{st.session_state.user}_messages"
    messages = st.session_state[messages_key]

    # Display chat history (skip system message)
    for msg in messages[1:]:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user"><strong>🧑 You:</strong> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )
        elif msg["role"] == "assistant":
            st.markdown(
                f'<div class="chat-assistant"><strong>🤖 Advisor:</strong> {msg["content"]}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # Message + file uploader form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask me about your ideal Computer Science course plan:",
            placeholder="E.g., I'm interested in AI. What should I take next?",
        )

        uploaded_files = st.file_uploader(
            "Add files (optional, like a degree plan, resume, CSV of courses):",
            accept_multiple_files=True,
            key="file_uploader",
        )

        submitted = st.form_submit_button("Send")

    # =========================
    # Handle message submission
    # =========================
    if submitted and (user_input or uploaded_files):

        if user_input:
            messages.append({"role": "user", "content": user_input})

        # Handle uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_bytes = uploaded_file.read()

                try:
                    content = file_bytes.decode("utf-8")
                    snippet = content[:4000]
                    messages.append({
                        "role": "user",
                        "content": f"[File uploaded: {uploaded_file.name}]\n\n{snippet}"
                    })
                except:
                    messages.append({
                        "role": "user",
                        "content": f"[File uploaded: {uploaded_file.name}] (binary file)"
                    })

        # Get response
        with st.spinner("Thinking like a Niner..."):
            if use_mock:
                combined_prompt = user_input or "(Files only)"
                answer = f"(Mock) This is a test response for: {combined_prompt}"
            else:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                    )
                    answer = response.choices[0].message.content
                except Exception as e:
                    st.error(f"OpenAI error: {e}")
                    answer = "(Error generating response.)"

        messages.append({"role": "assistant", "content": answer})
        save_user_data(st.session_state.user, messages)
        st.rerun()
