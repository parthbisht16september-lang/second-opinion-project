# Second Opinion — Adaptive AI Code Review Assistant

A Human-AI Interaction research tool that studies how the *style* of AI-generated code review feedback affects student trust and reliance — and adapts its explanation strategy based on each student's own behavior over time.

## Overview

Students submit code and receive an AI-generated review comment. The same underlying issue can be shown in one of three explanation styles:
- **Bare** — a plain statement of the issue
- **Confidence** — the issue with an added confidence score
- **Socratic** — the issue framed as a reflective question

After each interaction, the student responds by accepting, rejecting, or choosing to verify the suggestion first. The system logs this behavior and — for students in the adaptive condition — adjusts which explanation style is shown next, based on their recent pattern (e.g., a student who accepts everything without checking is nudged toward a more evidence-based style).

The goal is not to maximize trust in AI, but to study whether adapting explanation style improves **appropriately calibrated trust** — students learning when to rely on AI feedback and when to question it.

## Live App
🔗 [adaptivecodereview.streamlit.app](https://adaptivecodereview.streamlit.app)

## How It Works

1. **Code review generation** — student-submitted code is sent to an LLM (via Groq API) which identifies one issue
2. **Explanation formatting** — the raw issue is rendered in one of three styles depending on the student's current condition
3. **Behavior logging** — every interaction (style shown, action taken, decision time) is logged to a local database, tagged by student ID
4. **Adaptation** — for students in the adaptive condition, the system reviews their last few actions and selects the next explanation style accordingly

## Tech Stack
- Python
- Streamlit (interface)
- Groq API (LLM-based code review)
- SQLite (interaction logging)

## Project Files
- `app.py` — main Streamlit application
- `test_ai.py` — AI review generation logic
- `styles.py` — explanation style formatting
- `db.py` — logging and adaptation logic
- `requirements.txt` — dependencies

## Running Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

You'll need a Groq API key, added to `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your-key-here"
```

## Status
Currently in prototype/pilot testing phase, ahead of a planned in-class study with real student participants comparing the adaptive condition against a static (non-adaptive) baseline.
