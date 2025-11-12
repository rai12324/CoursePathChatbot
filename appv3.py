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

# api_key = os.getenv("OPENAI_API_KEY_TEST")
# st.sidebar.write(f"🔑 Loaded API Key: {'✅ Found' if api_key else '❌ Missing'}")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_NEW"))
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY_TEST"))

USER_DATA_DIR = "user_data"
os.makedirs(USER_DATA_DIR, exist_ok=True)

@st.cache_data
def load_courses():
    return pd.read_csv("courseTemp.csv")

df = load_courses()

course_summary = "\n".join(
    f"{row.course_id}: {row.course_name} ({row.concentration}) | Prerequisites: {row.prerequisites if pd.notna(row.prerequisites) else 'None'}"
    for _, row in df.iterrows()
)

st.title("🎓 CoursePath Chatbot")

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
    """Load saved messages/schedules for a user if they exist."""
    user_file = os.path.join(USER_DATA_DIR, f"{username}.json")
    if os.path.exists(user_file):
        with open(user_file, "r") as f:
            return json.load(f)
    else:
        # Start new session
        return [
            {
                "role": "system",
                "content": f"You are a helpful academic advisor. Use this course catalog:\n{course_summary}\nRecommend next courses respecting prerequisites."
            }
        ]

def save_user_data(username, data):
    """Save messages/schedules to disk."""
    user_file = os.path.join(USER_DATA_DIR, f"{username}.json")
    with open(user_file, "w") as f:
        json.dump(data, f, indent=2)

# =========================
# Authentication
# =========================
if st.sidebar.button("Login / Register"):
    if username:
        st.session_state.user = username
        # Load user session data from file if available
        st.session_state[f"{username}_messages"] = load_user_data(username)
        st.rerun()
    else:
        st.sidebar.error("Please enter a username to continue.")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# =========================
# Chat UI
# =========================
if st.session_state.user is None:
    st.info("👋 Please log in or register to begin chatting.")
else:
    st.subheader(f"Welcome, {st.session_state.user}!")

    messages_key = f"{st.session_state.user}_messages"
    messages = st.session_state[messages_key]

    # Display chat history
    for msg in messages[1:]:
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**🤖 Advisor:** {msg['content']}")

    # Input form to prevent message duplication
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask me about your ideal Computer Science course plan:")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        # Add user message
        messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            if use_mock:
                # Mock mode: no API cost
                answer = f"(Mock) This is a test response for: {user_input}"
            else:
                # Real OpenAI call
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        #model="gpt-3.5-turbo",
                        messages=messages,
                    )
                    answer = response.choices[0].message.content
                except Exception as e:
                    print("OpenAI error:", e)
                    print("Error type:", type(e))
                    if hasattr(e, 'http_status'):
                        print("HTTP status:", e.http_status)
                    if hasattr(e, 'code'):
                        print("Error code:", e.code)
                    if hasattr(e, 'user_message'):
                        print("User message:", e.user_message)

                    st.error(f"OpenAI error: {e}")
                    answer = "(Error generating response.)"

        # Add assistant response
        messages.append({"role": "assistant", "content": answer})

        # Save conversation persistently
        save_user_data(st.session_state.user, messages)

        # Refresh UI
        st.rerun()
