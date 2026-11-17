import html
import random
import time
import uuid

import streamlit as st

from test_ai import get_raw_issue
from styles import format_suggestion
from db import init_db, log_action, get_next_style


st.set_page_config(
    page_title="Adaptive Code Review",
    page_icon="🕵️",
    layout="centered",
)


# ---------- CUSTOM STYLING ----------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;700&family=Space+Mono:wght@400;700&display=swap');

    .stApp {
        background: radial-gradient(
            circle at 20% 0%,
            #241b42 0%,
            #16101f 45%,
            #0c0812 100%
        );
        color: #f2eefc;
    }

    html, body, [class*="css"] {
        font-family: 'Space Mono', monospace;
    }

    h1, h2, h3, .hero-title {
        font-family: 'Fredoka', sans-serif !important;
    }

    .hero {
        text-align: center;
        padding: 18px 0 8px 0;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 700;
        background: linear-gradient(
            90deg, #ff5e7e, #ff9a5c, #ffd76a
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-sub {
        color: #b8a9d9;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
    }

    .detective-card {
        background: linear-gradient(135deg, #2b2145, #1a1330);
        border: 1px solid #4a3a72;
        border-radius: 18px;
        padding: 22px 26px;
        margin: 14px 0;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }

    .avatar {
        font-size: 3rem;
        text-align: center;
    }

    .verdict-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1px;
        background: linear-gradient(90deg, #ff5e7e, #ffd76a);
        color: #1a1330;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- DATABASE ----------

try:
    init_db()
except Exception:
    st.error(
        "Could not connect to the study database. "
        "Please contact the study organiser."
    )
    st.stop()


# ---------- SESSION STATE ----------

# Each review keeps its own participant, style, and response status.
if "active_review" not in st.session_state:
    st.session_state.active_review = None


# ---------- RESPONSE HANDLER ----------

def save_response(action):
    review = st.session_state.active_review

    if review is None:
        return

    if review["response_saved"]:
        st.info("Your response to this review has already been saved.")
        return

    # Preserve the original decision time if a save needs to be retried.
    if review["pending_action"] is None:
        review["pending_action"] = action
        review["decision_time"] = max(
            0.0,
            time.monotonic() - review["start_time"],
        )

    try:
        log_action(
            review["student_id"],
            review["style"],
            review["pending_action"],
            review["decision_time"],
        )
    except Exception:
        st.error(
            "The database did not confirm the save. "
            "Please contact the study organiser before retrying."
        )
        return

    # Only mark saved after the database function succeeds.
    review["response_saved"] = True
    st.session_state.active_review = review
    st.rerun()


# ---------- HERO ----------

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🕵️ THE CODE DETECTIVE</div>
        <div class="hero-sub">
            Case files opened. Suspects: your bugs. Let's investigate.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")


# ---------- INPUT ----------

col_a, col_b = st.columns([1, 2])

with col_a:
    student_id = st.text_input(
        "🪪 Participant ID",
        help="Use the same assigned ID for every interaction.",
    )

code = st.text_area(
    "📂 Submit the evidence (your code)",
    height=170,
    placeholder="def suspicious_function():\n    ...",
)

avatars = ["🕵️", "🔍", "🧐", "🕵️‍♀️"]


# ---------- GENERATE REVIEW ----------

if st.button("🚨 OPEN THE CASE", use_container_width=True):
    clean_student_id = student_id.strip()

    if not clean_student_id:
        st.warning("Please enter your participant ID.")

    elif not code.strip():
        st.warning("Please enter some code to review.")

    else:
        # Clear the old review so a failed request cannot leave
        # old feedback appearing to belong to the new submission.
        st.session_state.active_review = None

        avatar = random.choice(avatars)

        try:
            with st.spinner(f"{avatar} Examining the evidence..."):
                style = get_next_style(clean_student_id)
                raw_issue = get_raw_issue(code)
                suggestion = format_suggestion(raw_issue, style)

            st.session_state.active_review = {
                "review_id": uuid.uuid4().hex,
                "student_id": clean_student_id,
                "code": code,
                "raw_issue": raw_issue,
                "suggestion": suggestion,
                "style": style,
                "avatar": avatar,
                "start_time": time.monotonic(),
                "response_saved": False,
                "pending_action": None,
                "decision_time": None,
            }

        except Exception:
            st.error(
                "Could not generate the review. "
                "Please try again. If this continues, "
                "contact the study organiser."
            )


# ---------- DISPLAY REVIEW ----------

review = st.session_state.active_review

if review is not None:
    # Escape AI-generated text before inserting it into HTML.
    safe_suggestion = html.escape(
        str(review["suggestion"])
    ).replace("\n", "<br>")

    st.markdown(
        f"""
        <div class="detective-card">
            <div class="avatar">{review["avatar"]}</div>

            <div style="text-align:center;">
                <span class="verdict-badge">CASE FINDING</span>
            </div>

            <p style="
                text-align:center;
                font-size:1.05rem;
                margin-top:10px;
            ">
                {safe_suggestion}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(f"Review for participant: {review['student_id']}")

    # Prevent responding to an old review after editing its inputs.
    inputs_changed = (
        student_id.strip() != review["student_id"]
        or code != review["code"]
    )

    if inputs_changed and not review["response_saved"]:
        st.warning(
            "The participant ID or code has changed. "
            "Restore the original inputs or click OPEN THE CASE "
            "to generate a new review."
        )

    save_uncertain = (
        review["pending_action"] is not None
        and not review["response_saved"]
    )

    disable_responses = (
        review["response_saved"]
        or inputs_changed
        or save_uncertain
    )

    st.markdown("#### 🧭 What's your verdict, detective?")

    col1, col2, col3 = st.columns(3)

    # Unique widget keys keep buttons associated with this review.
    review_id = review["review_id"]

    if col1.button(
        "✅ CASE CLOSED",
        key=f"accept_{review_id}",
        use_container_width=True,
        disabled=disable_responses,
    ):
        save_response("accept")

    if col2.button(
        "❌ NOT BUYING IT",
        key=f"reject_{review_id}",
        use_container_width=True,
        disabled=disable_responses,
    ):
        save_response("reject")

    if col3.button(
        "🔎 NEED MORE PROOF",
        key=f"verify_{review_id}",
        use_container_width=True,
        disabled=disable_responses,
    ):
        save_response("verify")

    if review["response_saved"]:
        st.info("Response saved. Submit another review to continue.")

    elif save_uncertain:
        st.warning(
            "Save status is uncertain. Ask the study organiser "
            "to check the database before continuing."
        )


# ---------- FOOTER ----------

st.write("")

st.markdown(
    """
    <p style="
        text-align:center;
        color:#6e5c99;
        font-size:0.75rem;
    ">
        SECOND OPINION RESEARCH PROJECT · HUMAN-AI INTERACTION STUDY
    </p>
    """,
    unsafe_allow_html=True,
)