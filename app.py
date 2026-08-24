import streamlit as st
import time
from test_ai import get_raw_issue
from styles import format_suggestion
from db import init_db, log_action

init_db()
st.title("Second Opinion — Code Review")

student_id = st.text_input("Enter your name/ID")
code = st.text_area("Paste your code here")

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if st.button("Get Review") and code and student_id:
    raw_issue = get_raw_issue(code)
    style = "bare"  # fixed for now — next phase makes this adaptive
    st.session_state.suggestion = format_suggestion(raw_issue, style)
    st.session_state.style = style
    st.session_state.start_time = time.time()

if "suggestion" in st.session_state:
    st.write(st.session_state.suggestion)
    col1, col2, col3 = st.columns(3)

    def handle(action):
        decision_time = time.time() - st.session_state.start_time
        log_action(student_id, st.session_state.style, action, decision_time)
        st.success(f"Logged: {action}")

    if col1.button("Accept"):
        handle("accept")
    if col2.button("Reject"):
        handle("reject")
    if col3.button("Verify First"):
        handle("verify")