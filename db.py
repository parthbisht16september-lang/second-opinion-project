import psycopg
import streamlit as st


def get_connection():
    config = st.secrets["postgres"]

    return psycopg.connect(
        host=config["host"],
        port=int(config["port"]),
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        sslmode=config.get("sslmode", "require"),
        connect_timeout=15,
    )


@st.cache_resource
def init_db():
    with get_connection() as conn:
        # Separate schema for this project's records.
        conn.execute("CREATE SCHEMA IF NOT EXISTS code_review")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS code_review.logs (
                id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                student_id TEXT NOT NULL,
                style TEXT NOT NULL,
                action TEXT NOT NULL
                    CHECK (action IN ('accept', 'reject', 'verify')),
                decision_time DOUBLE PRECISION NOT NULL
                    CHECK (decision_time >= 0),
                timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS logs_student_history_idx
            ON code_review.logs (student_id, id DESC)
        """)

    return True


def log_action(student_id, style, action, decision_time):
    student_id = student_id.strip()

    if not student_id:
        raise ValueError("A participant ID is required.")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO code_review.logs
                (student_id, style, action, decision_time)
            VALUES (%s, %s, %s, %s)
            """,
            (student_id, style, action, float(decision_time)),
        )


def get_student_history(student_id, limit=5):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT action
            FROM code_review.logs
            WHERE student_id = %s
            ORDER BY id DESC
            LIMIT %s
            """,
            (student_id.strip(), int(limit)),
        ).fetchall()

    return [row[0] for row in rows]


def get_next_style(student_id):
    history = get_student_history(student_id, limit=5)

    if len(history) < 3:
        return "bare"

    accept_rate = history.count("accept") / len(history)

    # Existing experimental rules; acceptance alone does not prove trust.
    if accept_rate > 0.7:
        return "confidence"
    elif accept_rate < 0.3:
        return "socratic"

    return "bare"