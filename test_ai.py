from groq import Groq
import streamlit as st

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def get_raw_issue(code):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": f"Review this code and point out ONE issue in one short sentence:\n\n{code}"}]
    )
    return response.choices[0].message.content