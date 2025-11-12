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
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

if "user" not in st.session_state:
    st.session_state.user = None

username = st.sidebar.text_input("Username")
if st.sidebar.button("Login / Register"):
    if username:
        st.session_state.user = username
        # Initialize message history for new users
        if f"{username}_messages" not in st.session_state:
            st.session_state[f"{username}_messages"] = [
                {
                    "role": "system",
                    "content": f"You are a helpful academic advisor. Use this course catalog:\n{course_summary}\nRecommend next courses respecting prerequisites."
                }
            ]
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

    # Display chat history
    for msg in st.session_state[messages_key][1:]:
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**🤖 Advisor:** {msg['content']}")

    # Input form to prevent message duplication
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Ask me about your ideal Computer Science course plan:")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        # Add user message to chat history
        st.session_state[messages_key].append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            if use_mock:
                # --- MOCK RESPONSE (no API cost) ---
                answer = f"(Mock) This is a test response for: {user_input}"
            else:
                # --- REAL OPENAI CALL ---
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state[messages_key],
                    )
                    answer = response.choices[0].message.content
                except Exception as e:
                    st.error(f"OpenAI error: {e}")
                    answer = "(Error generating response.)"

        # Add assistant message
        st.session_state[messages_key].append({"role": "assistant", "content": answer})

        # Rerun app to refresh UI
        st.rerun()
