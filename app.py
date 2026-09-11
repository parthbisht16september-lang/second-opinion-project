import streamlit as st
import time
import random
from test_ai import get_raw_issue
from styles import format_suggestion
from db import init_db, log_action, get_next_style

st.set_page_config(page_title="Adaptive Code Review", page_icon="🕵️", layout="centered")

# ---------- CUSTOM STYLING ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;700&family=Space+Mono:wght@400;700&display=swap');

.stApp {
    background: radial-gradient(circle at 20% 0%, #241b42 0%, #16101f 45%, #0c0812 100%);
    color: #f2eefc;
}
html, body, [class*="css"] { font-family: 'Space Mono', monospace; }
h1, h2, h3, .hero-title { font-family: 'Fredoka', sans-serif !important; }

.hero { text-align: center; padding: 18px 0 8px 0; }
.hero-title {
    font-size: 2.6rem; font-weight: 700;
    background: linear-gradient(90deg, #ff5e7e, #ff9a5c, #ffd76a);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color: #b8a9d9; font-size: 0.95rem; letter-spacing: 0.5px; }

.detective-card {
    background: linear-gradient(135deg, #2b2145, #1a1330);
    border: 1px solid #4a3a72; border-radius: 18px;
    padding: 22px 26px; margin: 14px 0;
    box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    animation: float 3.5s ease-in-out infinite;
}
@keyframes float { 0%,100% { transform: translateY(0px); } 50% { transform: translateY(-6px); } }

.avatar { font-size: 3rem; text-align: center; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }

.verdict-badge {
    display: inline-block; padding: 4px 14px; border-radius: 999px;
    font-size: 0.75rem; font-weight: 700; letter-spacing: 1px;
    background: linear-gradient(90deg, #ff5e7e, #ffd76a); color: #1a1330;
}

.stButton>button { border-radius: 12px !important; font-weight: 700 !important; border: none !important; transition: transform 0.15s ease !important; }
.stButton>button:hover { transform: scale(1.04); }
</style>
""", unsafe_allow_html=True)

init_db()

# ---------- HERO ----------
st.markdown("""
<div class="hero">
    <div class="hero-title">🕵️ THE CODE DETECTIVE</div>
    <div class="hero-sub">Case files opened. Suspects: your bugs. Let's investigate.</div>
</div>
""", unsafe_allow_html=True)

st.write("")

# ---------- INPUT ----------
col_a, col_b = st.columns([1, 2])
with col_a:
    student_id = st.text_input("🪪 Detective badge # (your name)")
code = st.text_area("📂 Submit the evidence (your code)", height=170, placeholder="def suspicious_function():\n    ...")

if "start_time" not in st.session_state:
    st.session_state.start_time = None

avatars = ["🕵️", "🔍", "🧐", "🕵️‍♀️"]

if st.button("🚨 OPEN THE CASE", use_container_width=True) and code and student_id:
    avatar = random.choice(avatars)
    with st.spinner(f"{avatar} Examining the evidence..."):
        raw_issue = get_raw_issue(code)
        style = get_next_style(student_id)  # adaptive logic starts from here
        st.session_state.suggestion = format_suggestion(raw_issue, style)
        st.session_state.style = style
        st.session_state.start_time = time.time()
        st.session_state.avatar = avatar

# ---------- VERDICT ----------
if "suggestion" in st.session_state:
    st.markdown(f"""
    <div class="detective-card">
        <div class="avatar">{st.session_state.get('avatar','🕵️')}</div>
        <div style="text-align:center;"><span class="verdict-badge">CASE FINDING</span></div>
        <p style="text-align:center; font-size:1.05rem; margin-top:10px;">
            {st.session_state.suggestion}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🧭 What's your verdict, detective?")
    col1, col2, col3 = st.columns(3)

    def handle(action, msg):
    decision_time = time.time() - st.session_state.start_time
    log_action(student_id, st.session_state.style, action, decision_time)

    if action == "accept":
        st.success(f"✅ {msg}")
        st.balloons()
    elif action == "reject":
        st.error(f"❌ {msg}")
        st.snow()
    elif action == "verify":
        st.warning(f"🔎 {msg}")

if col1.button("✅ CASE CLOSED", use_container_width=True):
    handle("accept", "Case closed — trusted the finding!")
if col2.button("❌ NOT BUYING IT", use_container_width=True):
    handle("reject", "Rejected — detective's gut says no.")
if col3.button("🔎 NEED MORE PROOF", use_container_width=True):
    handle("verify", "Flagged for further investigation. Digging deeper...")
st.write("")
st.markdown(
    "<p style='text-align:center; color:#6e5c99; font-size:0.75rem;'>SECOND OPINION RESEARCH PROJECT · HUMAN-AI INTERACTION STUDY</p>",
    unsafe_allow_html=True
)