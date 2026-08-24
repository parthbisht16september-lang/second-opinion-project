import streamlit as st
import time
from test_ai import get_raw_issue
from styles import format_suggestion
from db import init_db, log_action

st.set_page_config(page_title="Adaptive Code Review", page_icon="🤖", layout="centered")

init_db()

# --- Header ---
st.markdown(
    """
    <div style="text-align:center; padding: 10px 0;">
        <h1>🤖 Adaptive Code Review</h1>
        <p style="color:gray;">Your code, reviewed by AI — explained your way.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# --- Input section ---
col_a, col_b = st.columns([1, 2])
with col_a:
    student_id = st.text_input("👤 Your name/ID")
with col_b:
    st.write("")  # spacing

code = st.text_area("💻 Paste your code here", height=180, placeholder="def my_function():\n    pass")

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# --- Get Review button ---
if st.button("🔍 Get Review", use_container_width=True) and code and student_id:
    with st.spinner("🤔 AI is analyzing your code..."):
        time.sleep(0.5)  # small pause for effect
        raw_issue = get_raw_issue(code)
        style = "bare"  # fixed for now — adaptive logic plugs in here
        st.session_state.suggestion = format_suggestion(raw_issue, style)
        st.session_state.style = style
        st.session_state.start_time = time.time()

# --- Show suggestion ---
if "suggestion" in st.session_state:
    st.divider()
    st.markdown("### 💡 AI's Feedback")
    st.info(st.session_state.suggestion)

    st.markdown("#### What do you want to do?")
    col1, col2, col3 = st.columns(3)

    def handle(action, emoji, message):
        decision_time = time.time() - st.session_state.start_time
        log_action(student_id, st.session_state.style, action, decision_time)
        st.toast(f"{emoji} {message}", icon=emoji)
        if action == "accept":
            st.balloons()

    if col1.button("✅ Accept", use_container_width=True):
        handle("accept", "✅", "Logged: Accepted")
    if col2.button("❌ Reject", use_container_width=True):
        handle("reject", "❌", "Logged: Rejected")
    if col3.button("🔎 Verify First", use_container_width=True):
        handle("verify", "🔎", "Logged: Verifying first")

    st.caption(f"⏱️ Style shown: `{st.session_state.style}`")

st.divider()
st.caption("Built for a Human-AI Interaction research study · Second Opinion Project")