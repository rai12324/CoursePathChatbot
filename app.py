import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

# Load API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load CSV file
@st.cache_data
def load_courses():
    df = pd.read_csv("courses.csv")
    return df

df = load_courses()

# Prepare a short text summary of the data for GPT
course_summary = "\n".join(
    f"{row.course_id}: {row.course_name} ({row.concentration}) | Prerequisites: {row.prerequisites if pd.notna(row.prerequisites) else 'None'}"
    for _, row in df.iterrows()
)

# Streamlit UI
st.title("🎓 CoursePath Chatbot")
st.write("Ask me about your ideal Computer Science course plan!")

user_input = st.text_input("Enter your question:")

if user_input:
    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful academic advisor. Use this course catalog:\n{course_summary}\nRecommend next courses respecting prerequisites.",
                },
                {"role": "user", "content": user_input},
            ],
        )

        answer = response.choices[0].message.content
        st.markdown("### 💬 Chatbot Response:")
        st.write(answer)
