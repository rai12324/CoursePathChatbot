import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

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

# --- LOGIN SECTION ---
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    username = st.text_input("👋 Enter your username to log in or register:")
    if st.button("Login / Register") and username:
        st.session_state.user = username
        if f"{username}_messages" not in st.session_state:
            st.session_state[f"{username}_messages"] = [
                {"role": "system", "content": f"You are a helpful academic advisor. Use this course catalog:\n{course_summary}"}
            ]
        st.rerun()
else:
    st.write(f"👋 Hello, **{st.session_state.user}**!")
    messages_key = f"{st.session_state.user}_messages"

    # Display chat history
    for msg in st.session_state[messages_key][1:]:
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**🤖 Advisor:** {msg['content']}")

    # Input box for user question
    user_input = st.text_input("Ask me about your ideal Computer Science course plan:")

    if user_input:
        # Add user message
        st.session_state[messages_key].append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state[messages_key],
            )

        answer = response.choices[0].message.content
        st.session_state[messages_key].append({"role": "assistant", "content": answer})
        st.rerun()

    # if user_input:
    #     st.session_state[messages_key].append({"role": "user", "content": user_input})

    #     with st.spinner("Thinking..."):
    #         try:
    #             # 🧠 Replace this real call temporarily:
    #             # response = client.chat.completions.create(
    #             #     model="gpt-4o-mini",
    #             #     messages=st.session_state[messages_key],
    #             # )

    #             # ✅ Mock response for testing (no API usage)
    #             class MockChoice:
    #                 def __init__(self, content):
    #                     self.message = type("m", (), {"content": content})

    #             response = type("r", (), {"choices": [MockChoice(f"(Mock) This is a test response for: {user_input}")]})


    #             # If you want, simulate latency:
    #             # import time; time.sleep(1)

    #             answer = response.choices[0].message.content

    #         except Exception as e:
    #             st.error(f"Error during processing: {e}")
    #             answer = "(Mock) Error encountered."

    #     st.session_state[messages_key].append({"role": "assistant", "content": answer})
    #     st.rerun()

