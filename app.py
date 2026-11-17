"""Code Detective UI. Uses the existing PostgreSQL db.py and AI modules.

The session journal is browser-session-only. PostgreSQL still stores the
existing log_action fields; full review persistence is a separate upgrade.
"""
import html
import logging
import time
import uuid
from datetime import datetime, timezone

import streamlit as st
from db import init_db, log_action, get_next_style
from test_ai import get_raw_issue
from styles import format_suggestion

st.set_page_config(page_title="Code Detective · Review Studio", page_icon="◈", layout="wide")
logger = logging.getLogger(__name__)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root {color-scheme:dark;}
.stApp {background:radial-gradient(ellipse at 90% 0%,#20234b 0%,#101425 40%,#0b0f1a 85%);color:#e8edf7;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stSidebar"] {background:#101522;border-right:1px solid #263047;}
.block-container {max-width:1440px;padding-top:2.2rem;padding-bottom:3rem;}
html,body,[data-testid="stAppViewContainer"] {font-family:'DM Sans',sans-serif;}
h1,h2,h3 {font-family:'Space Grotesk',sans-serif!important;color:#f0f3ff!important;}
p,label,[data-testid="stCaptionContainer"] {color:#abb7cf;}
.stTextInput input,.stTextArea textarea {background:#101827!important;color:#e8edf7!important;border:1px solid #303e58!important;border-radius:12px!important;}
.stTextArea textarea {font-family:ui-monospace,SFMono-Regular,monospace!important;font-size:14px!important;line-height:1.7!important;}
.stButton button,.stDownloadButton button {border-radius:11px!important;border:1px solid #36435f!important;background:#182239;color:#ecf1ff;min-height:46px;transition:transform .15s,border-color .15s;}
.stButton button:hover {border-color:#8a9fff!important;transform:translateY(-1px);}
.stButton button[kind="primary"] {background:#a9b8ff!important;color:#10172f!important;border-color:#a9b8ff!important;}
.stButton button:disabled {opacity:.45;transform:none;}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#2b3650!important;border-radius:17px!important;}
button[data-baseweb="tab"] {color:#aebbd4!important;font-size:15px;}
button[data-baseweb="tab"][aria-selected="true"] {color:#c3cdff!important;}
[data-testid="stMetricValue"] {color:#eef2ff;font-family:'Space Grotesk',sans-serif;}
[data-testid="stExpander"] {border-color:#303c54;border-radius:12px;}
.brand {font:700 22px 'Space Grotesk',sans-serif;color:#eff2ff;letter-spacing:-.6px;}
.brand span {color:#b3c1ff;}
.eyebrow {color:#9dacf0;font-size:11px;font-weight:700;letter-spacing:2.4px;text-transform:uppercase;margin-bottom:12px;}
.hero {padding:25px 0 28px;}
.hero h1 {font-size:clamp(32px,4vw,53px);line-height:1.08;letter-spacing:-2px;margin:0 0 15px;}
.hero p {font-size:16px;max-width:680px;line-height:1.7;margin:0;}
.pill {display:inline-block;border:1px solid #394768;background:#18233a;color:#bdcaff;padding:6px 12px;border-radius:30px;font-size:11px;letter-spacing:.6px;}
.flow {display:flex;gap:10px;flex-wrap:wrap;margin:0 0 25px;}
.step {flex:1;min-width:150px;padding:13px 16px;border:1px solid #2b3650;border-radius:12px;color:#7887a6;font-size:13px;background:#111a2a;}
.step.active {border-color:#8295e1;color:#e1e7ff;background:#202d49;}
.step.done {color:#b5c3e3;border-color:#455677;}
.finding {background:linear-gradient(130deg,#253252,#171f33);border:1px solid #45547c;border-radius:17px;padding:28px;margin:12px 0 18px;animation:arrive .3s ease-out;}
.finding .copy {color:#f0f3ff;font:500 19px/1.75 'DM Sans',sans-serif;overflow-wrap:anywhere;}
.empty {min-height:275px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;border:1px dashed #364361;border-radius:17px;padding:25px;background:#121a2a;}
.empty .orb {font-size:44px;color:#a2b4ff;margin-bottom:15px;}
.empty h3 {font-size:21px!important;}
.empty p {font-size:14px;max-width:300px;}
.micro {font-size:12px;color:#8998b4;line-height:1.7;}
.footer {border-top:1px solid #26314a;padding-top:20px;margin-top:32px;color:#8290ac;font-size:12px;}
@keyframes arrive {from {opacity:0;transform:translateY(5px)} to {opacity:1;transform:translateY(0)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;}}
@media(max-width:700px){.block-container{padding:1.3rem 1rem}.hero h1{font-size:34px}.finding{padding:20px}.step{min-width:100px}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# A new state namespace avoids stale state from previous app.py versions.
for key, default in {"studio_person":"", "studio_review":None, "studio_journal":[], "studio_code":""}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def markup(value):
    return html.escape(str(value)).replace("\n", "<br>")


def report_error(message, exc):
    # No exception text is displayed because connection errors may contain details.
    logger.error("%s (%s)", message, type(exc).__name__)
    st.error(message)


try:
    init_db()
except Exception as exc:
    report_error("The database connection is unavailable. Please contact the organiser.", exc)
    st.stop()


def begin_session():
    person = st.session_state.get("studio_identity", "").strip()
    if not person:
        st.session_state["studio_identity_error"] = True
        return
    st.session_state.studio_person = person
    st.session_state.studio_review = None
    st.session_state.studio_journal = []
    st.session_state.studio_code = ""
    st.session_state["studio_identity_error"] = False


def end_session():
    st.session_state.studio_person = ""
    st.session_state.studio_review = None
    st.session_state.studio_journal = []
    st.session_state.studio_code = ""


def new_review():
    st.session_state.studio_review = None
    # Preserve the code to make revisions easy.


def record_response(action):
    review = st.session_state.studio_review
    if not review or review["state"] != "ready":
        return
    review["state"] = "saving"
    review["action"] = action
    review["decision_time"] = max(0.0, time.monotonic() - review["start_time"])
    try:
        log_action(review["student_id"], review["style"], action, review["decision_time"])
    except Exception as exc:
        # Do not automatically retry a write whose outcome may be uncertain.
        review["state"] = "uncertain"
        logger.error("Response save failed (%s)", type(exc).__name__)
        return
    review["state"] = "saved"
    st.session_state.studio_journal.append(dict(review))


person = st.session_state.studio_person
review = st.session_state.studio_review
journal = st.session_state.studio_journal

with st.sidebar:
    st.markdown('<div class="brand"><span>◈</span> Code Detective</div>', unsafe_allow_html=True)
    st.caption("SECOND OPINION · REVIEW STUDIO")
    st.divider()
    if not person:
        st.subheader("Start your session")
        st.text_input("Assigned participant ID", key="studio_identity", placeholder="e.g. P01", max_chars=80)
        st.button("Enter workspace →", on_click=begin_session, type="primary", use_container_width=True)
        if st.session_state.get("studio_identity_error"):
            st.warning("Enter your assigned participant ID first.")
        st.caption("Use the same ID on every visit. IDs are identifiers, not passwords.")
    else:
        st.markdown('<span class="pill">SESSION ACTIVE</span>', unsafe_allow_html=True)
        st.subheader(person)
        st.caption("Your ID is fixed for this session.")
        st.metric("Responses saved this session", len(journal))
        st.caption("This count resets on refresh. Saved database records remain.")
        st.divider()
        st.button("End session / change participant", on_click=end_session, use_container_width=True,
                  disabled=bool(review and review["state"] in ("ready", "saving", "uncertain")))
        st.caption("Finish the current review before changing participants.")
    st.divider()
    with st.expander("How the session works", expanded=True):
        st.write("1. Submit your Python code.\n2. Read the review carefully.\n3. Accept, reject, or choose to verify.")
        st.caption("All three choices are equally valid. AI feedback may be incorrect.")
    st.markdown('<div class="micro">Your code is sent to the configured AI provider for review. Avoid including passwords or private information.</div>', unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">Human × AI · Code review workspace</div><h1>A second opinion.<br>Your final decision.</h1><p>Explore your code, examine the feedback, and decide what deserves your trust.</p></div>', unsafe_allow_html=True)
phase = 0 if not person else 3 if review and review["state"] == "saved" else 2 if review else 1
steps = ["01 · Identify", "02 · Submit code", "03 · Consider feedback", "04 · Response saved"]
st.markdown('<div class="flow">' + ''.join(f'<div class="step {"done" if i < phase else "active" if i == phase else ""}">{label}</div>' for i,label in enumerate(steps)) + '</div>', unsafe_allow_html=True)

if not person:
    with st.container(border=True):
        st.subheader("Your workspace is ready")
        st.write("Enter your assigned participant ID in the sidebar to begin. On a narrow screen, open the sidebar using the arrow at the top left.")
    st.stop()

workspace, history, guide = st.tabs(["◈  Review workspace", "↺  Session journal", "ⓘ  Participant guide"])
with workspace:
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown("### 01 / Your code")
        st.caption("Python · Your code is reviewed, not executed by this app.")
        locked = bool(review)
        st.text_area("Python source", key="studio_code", height=310, disabled=locked,
                     placeholder='def your_function(value):\n    """Describe what the function should do."""\n    return value')
        code = st.session_state.studio_code
        st.caption(f"{len(code.splitlines())} lines · {len(code)} characters")
        if not review:
            if st.button("Review my code →", type="primary", use_container_width=True, disabled=not code.strip()):
                with st.status("Preparing your review…", expanded=True) as status:
                    try:
                        st.write("Reading recent interaction history…")
                        style = get_next_style(person)
                        st.write("Requesting AI feedback…")
                        issue = get_raw_issue(code)
                        if not isinstance(issue,str) or not issue.strip():
                            raise ValueError("Empty review")
                        suggestion = format_suggestion(issue, style)
                        st.session_state.studio_review = {
                            "review_id":uuid.uuid4().hex, "student_id":person, "code":code,
                            "raw_issue":issue, "suggestion":suggestion, "style":style,
                            "created_at":datetime.now(timezone.utc).isoformat(),
                            "state":"ready", "action":None, "decision_time":None,
                        }
                        status.update(label="Review ready", state="complete", expanded=False)
                    except Exception as exc:
                        status.update(label="Review could not be generated", state="error")
                        report_error("The request failed. Your code is preserved; you can try again.", exc)
                if st.session_state.studio_review:
                    st.rerun()
        elif review["state"] == "saved":
            st.button("Start next review →", on_click=new_review, type="primary", use_container_width=True)
            st.caption("Your previous code stays in the editor so you can revise it.")
        else:
            st.info("Code is locked to this review. Record your response to continue.")
    with right:
        st.markdown("### 02 / A second opinion")
        st.caption("Read the finding, then make your own judgement.")
        if review is None:
            st.markdown('<div class="empty"><div class="orb">◈</div><h3>Room for a fresh perspective</h3><p>Your review will appear here after you submit code.</p></div>', unsafe_allow_html=True)
        else:
            # No whitespace-indented multiline HTML: prevents Markdown code blocks.
            st.markdown('<div class="finding"><div class="eyebrow">Review finding</div><div class="copy">' + markup(review["suggestion"]) + '</div></div>', unsafe_allow_html=True)
            if "start_time" not in review:
                review["start_time"] = time.monotonic()
            if review["style"] == "confidence":
                st.caption("The 78% cue in this prototype is illustrative, not a measured probability of correctness.")
            st.markdown("#### 03 / Your decision")
            st.caption("Choose what you would do with this feedback.")
            buttons = st.columns(3)
            for col, action, label in zip(buttons, ["accept","reject","verify"], ["Accept", "Reject", "Verify first"]):
                col.button(label, key=f'{review["review_id"]}_{action}', on_click=record_response,
                           args=(action,), disabled=review["state"] != "ready", use_container_width=True)
            st.caption("Accept: use the feedback · Reject: do not use it · Verify: check before deciding.")
            if review["state"] == "saved":
                st.success("Response saved. You can start your next review.")
                st.caption("Recorded choice: " + review["action"].capitalize())
            elif review["state"] == "uncertain":
                st.error("Save status is uncertain. Do not resubmit. Ask the organiser to check the database before refreshing.")
            with st.expander("View the submitted code"):
                st.code(review["code"], language="python")

with history:
    st.subheader("Your session journal")
    st.caption("Only responses saved in this browser session appear here. This is not the complete database history.")
    if not journal:
        st.info("Your first saved response will appear here.")
    else:
        for index, entry in reversed(list(enumerate(journal, start=1))):
            with st.expander(f'Review {index:02d} · {entry["action"].capitalize()} · {entry["created_at"][11:19]} UTC'):
                st.write(entry["suggestion"])
                st.code(entry["code"], language="python")
                st.caption(f'Response recorded after {entry["decision_time"]:.1f} seconds. Timing includes time spent away from the page.')
        st.caption("Refreshing clears these local review details. The existing database log remains saved.")

with guide:
    st.subheader("Keep your judgement in the loop")
    a,b,c = st.columns(3)
    for col,title,body in [(a,"Accept","You agree with the feedback and would use it."),(b,"Reject","You disagree with the feedback or would not use it."),(c,"Verify first","You want to check the feedback before deciding.")]:
        with col:
            with st.container(border=True):
                st.markdown(f"#### {title}")
                st.write(body)
    st.info("Selecting Verify first records your intention to verify. This version does not run tests or track external verification.")
    st.write("Use your assigned ID consistently. Submit your own code and describe its intended behaviour in a comment or docstring when needed.")
    st.caption("There is no reward for accepting feedback and no penalty for rejecting it.")

st.markdown('<div class="footer">◈ CODE DETECTIVE &nbsp; / &nbsp; Second Opinion research prototype &nbsp; · &nbsp; Human–AI interaction</div>', unsafe_allow_html=True)
