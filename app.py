"""
GEAB RevOps Analyst - SQL Assessment App
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
import json
import os
from datetime import datetime
from scoring import QUESTIONS, score_all, run_query, get_connection
from seed_db import ensure_db

# Auto-seed database if missing
ensure_db()

st.set_page_config(
    page_title="GEAB SQL Assessment",
    page_icon="\U0001F4CA",
    layout="wide",
)

st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; }
    .geab-header {
        background: linear-gradient(135deg, #1B5E20, #2E7D32);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .geab-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; color: white; }
    .geab-header .subtitle { font-size: 0.9rem; opacity: 0.85; margin-top: 0.2rem; }
    .tier-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        color: white;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .tier-foundation { background: #43A047; }
    .tier-intermediate { background: #FB8C00; }
    .tier-advanced { background: #E53935; }
    .tier-expert { background: #6A1B9A; }
    .question-card {
        background: #FAFAFA;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .question-card h3 { margin-top: 0; color: #1B5E20; }
    .timer-box {
        background: #FFF3E0;
        border: 2px solid #FB8C00;
        border-radius: 10px;
        padding: 0.8rem 1.2rem;
        text-align: center;
        font-size: 1.8rem;
        font-weight: 700;
        color: #E65100;
    }
    .timer-box.urgent {
        background: #FFEBEE;
        border-color: #E53935;
        color: #B71C1C;
        animation: pulse 1s infinite;
    }
    .timer-box.idle {
        background: #ECEFF1;
        border-color: #90A4AE;
        color: #455A64;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .score-card {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .score-card .big-score {
        font-size: 3.5rem;
        font-weight: 800;
        color: #1B5E20;
    }
    .score-card .tier-label {
        font-size: 1.4rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .feedback-correct { border-left: 4px solid #43A047; padding-left: 1rem; margin: 0.5rem 0; }
    .feedback-partial { border-left: 4px solid #FB8C00; padding-left: 1rem; margin: 0.5rem 0; }
    .feedback-wrong { border-left: 4px solid #E53935; padding-left: 1rem; margin: 0.5rem 0; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

defaults = {
    "stage": "login",
    "candidate_name": "",
    "start_time": None,
    "answers": {},
    "results": None,
    "summary": None,
    "submitted": False,
    "time_up": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

TIME_LIMIT_SECONDS = 45 * 60


def get_remaining_time():
    if st.session_state.start_time is None:
        return TIME_LIMIT_SECONDS
    elapsed = time.time() - st.session_state.start_time
    return max(0, TIME_LIMIT_SECONDS - elapsed)


def format_time(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def tier_badge_html(tier):
    css_class = f"tier-{tier.lower()}"
    return f'<span class="tier-badge {css_class}">{tier}</span>'


def save_submission(name, answers, results, summary):
    submissions_dir = os.path.join(os.path.dirname(__file__), "submissions")
    os.makedirs(submissions_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name.replace(' ', '_')}_{timestamp}.json"
    data = {
        "candidate": name,
        "submitted_at": datetime.now().isoformat(),
        "answers": {str(k): v for k, v in answers.items()},
        "results": results,
        "summary": summary,
    }
    filepath = os.path.join(submissions_dir, filename)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    return filepath


def render_sidebar():
    """Shared schema sidebar, used by both review and assessment stages."""
    with st.sidebar:
        st.markdown("### Database Schema")
        st.markdown("**Customer**")
        st.code("Cust_Id (PK)\nMembership_No\nJoined_Date", language=None)
        st.markdown("**Contact**")
        st.code("Contact_Id (PK)\nFull_Name\nAddress_Id (FK)\nPhone_Number\nCust_Id (FK)\nCreated_Date", language=None)
        st.markdown("**Address**")
        st.code("Address_Id (PK)\nAddress_Line_1\nPostcode\nContact_Id (FK)", language=None)
        st.markdown("**Rental_History**")
        st.code("History_Id (PK)\nVideo_Id (FK)\nRental_Start_Date\nRental_End_Date\nCust_Id (FK)", language=None)
        st.markdown("**Videos**")
        st.code("Video_Id (PK)\nFilm_Name\nGenre\nRelease_Year\nDaily_Rate", language=None)
        st.markdown("---")
        st.markdown("**Relationships:**")
        st.markdown(
            "Customer \u2192 Contact (Cust_Id)\n\n"
            "Contact \u2192 Address (Address_Id)\n\n"
            "Customer \u2192 Rental_History (Cust_Id)\n\n"
            "Rental_History \u2192 Videos (Video_Id)"
        )
        st.markdown("---")
        st.markdown("**Notes:**")
        st.markdown(
            "- Daily_Rate = cost per day to rent\n"
            "- NULL Rental_End_Date = still on loan\n"
            "- Only SELECT queries are permitted"
        )


def render_questions_and_inputs():
    """Shared question tabs + SQL inputs + Test Query buttons, used by both review and assessment."""
    tiers = ["Foundation", "Intermediate", "Advanced", "Expert"]
    tabs = st.tabs(tiers)

    tier_questions = {}
    for q in QUESTIONS:
        tier_questions.setdefault(q["tier"], []).append(q)

    for tab, tier in zip(tabs, tiers):
        with tab:
            for q in tier_questions.get(tier, []):
                st.markdown(f"""
                <div class="question-card">
                    <h3>Q{q['id']}. {q['title']} &nbsp; {tier_badge_html(q['tier'])} &nbsp;
                    <span style="color: #9E9E9E; font-size: 0.85rem;">[{q['points']} pt{'s' if q['points'] > 1 else ''}]</span></h3>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(q["text"])
                if q["hint"]:
                    st.caption(f"Hint: {q['hint']}")

                sql_key = f"sql_{q['id']}"
                sql_input = st.text_area(
                    "Your SQL:",
                    value=st.session_state.answers.get(q["id"], ""),
                    height=150,
                    key=sql_key,
                    label_visibility="collapsed",
                    placeholder="Write your SQL query here...",
                )
                st.session_state.answers[q["id"]] = sql_input

                col_test, col_spacer = st.columns([1, 3])
                with col_test:
                    if st.button(f"Test Query", key=f"test_{q['id']}"):
                        if sql_input.strip():
                            try:
                                cols, rows = run_query(sql_input.strip().rstrip(";"))
                                st.success(f"Query returned {len(rows)} rows.")
                                if rows:
                                    import pandas as pd
                                    df = pd.DataFrame(rows[:10], columns=cols)
                                    st.dataframe(df, use_container_width=True)
                                    if len(rows) > 10:
                                        st.caption(f"Showing first 10 of {len(rows)} rows.")
                            except Exception as e:
                                st.error(f"SQL Error: {e}")
                        else:
                            st.warning("Enter a query first.")

                st.markdown("---")


# =====================
# LOGIN SCREEN
# =====================
if st.session_state.stage == "login":
    st.markdown("""
    <div class="geab-header">
        <div>
            <h1>GEAB SQL Assessment</h1>
            <div class="subtitle">RevOps Analyst Role</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Welcome")
        st.markdown(
            "This assessment tests your SQL skills against a live database. "
            "You have **45 minutes** to answer 8 questions of increasing difficulty. "
            "Your queries will be executed against a real database and auto-scored."
        )
        st.markdown("---")
        st.markdown("**How it works:**")
        st.markdown(
            "- After entering your name, you'll see a **review screen** with all questions and the database schema\n"
            "- You can draft and test your queries on the review screen — **the timer does not start yet**\n"
            "- When you click **Start Timer**, the 45-minute countdown begins\n"
            "- Questions are grouped into four tiers: Foundation, Intermediate, Advanced, and Expert\n"
            "- You are not expected to answer every question\n"
            "- Partial credit is awarded where logic is sound\n"
            "- Only SELECT queries are permitted"
        )
        st.markdown("---")
        st.markdown("**Scoring:**")
        scoring_data = {
            "Tier": ["Foundation (Q1-Q3)", "Intermediate (Q4-Q5)", "Advanced (Q6-Q7)", "Expert (Q8)"],
            "Points": ["3", "5", "8", "5"],
            "Cumulative": ["0-3", "4-8", "9-16", "17-21"],
        }
        st.table(scoring_data)
        st.markdown("---")
        name = st.text_input("Enter your full name to begin:", key="name_input")
        if st.button("Continue to Review", type="primary", use_container_width=True):
            if name.strip():
                st.session_state.candidate_name = name.strip()
                st.session_state.stage = "review"
                st.rerun()
            else:
                st.error("Please enter your name.")


# =====================
# REVIEW SCREEN (timer not yet started)
# =====================
elif st.session_state.stage == "review":
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"""
        <div class="geab-header">
            <div>
                <h1>Review &amp; Pre-Draft</h1>
                <div class="subtitle">Candidate: {st.session_state.candidate_name} &mdash; Timer not started</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with header_col2:
        st.markdown(f"""
        <div class="timer-box idle">
            {format_time(TIME_LIMIT_SECONDS)}
        </div>
        """, unsafe_allow_html=True)

    st.info(
        "Take a moment to review the schema (left) and the questions below. "
        "You can draft and test queries now — **the timer has not started yet**. "
        "When you're ready, scroll to the bottom and click **Start Timer** to begin the 45-minute assessment. "
        "Anything you've drafted will carry over."
    )

    render_sidebar()
    render_questions_and_inputs()

    st.markdown("")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("Start Timer & Begin Assessment", type="primary", use_container_width=True):
            st.session_state.start_time = time.time()
            st.session_state.stage = "assessment"
            st.rerun()


# =====================
# ASSESSMENT SCREEN
# =====================
elif st.session_state.stage == "assessment":
    # Auto-refresh every second so the timer ticks down in real time.
    # debounce=True (default) means refreshes pause briefly while the candidate is typing,
    # so it won't interrupt them writing queries.
    st_autorefresh(interval=1000, key="assessment_timer_tick")

    remaining = get_remaining_time()

    if remaining <= 0 and not st.session_state.submitted:
        st.session_state.time_up = True
        st.session_state.submitted = True
        results, summary = score_all(st.session_state.answers)
        st.session_state.results = results
        st.session_state.summary = summary
        save_submission(st.session_state.candidate_name, st.session_state.answers, results, summary)
        st.session_state.stage = "results"
        st.rerun()

    urgent_class = "urgent" if remaining < 300 else ""
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(f"""
        <div class="geab-header">
            <div>
                <h1>SQL Assessment</h1>
                <div class="subtitle">Candidate: {st.session_state.candidate_name}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with header_col2:
        st.markdown(f"""
        <div class="timer-box {urgent_class}">
            {format_time(remaining)}
        </div>
        """, unsafe_allow_html=True)

    render_sidebar()
    render_questions_and_inputs()

    st.markdown("")
    col_sub1, col_sub2, col_sub3 = st.columns([1, 2, 1])
    with col_sub2:
        if st.button("Submit Assessment", type="primary", use_container_width=True):
            answered = sum(1 for v in st.session_state.answers.values() if v.strip())
            if answered == 0:
                st.error("Please answer at least one question before submitting.")
            else:
                results, summary = score_all(st.session_state.answers)
                st.session_state.results = results
                st.session_state.summary = summary
                st.session_state.submitted = True
                save_submission(st.session_state.candidate_name, st.session_state.answers, results, summary)
                st.session_state.stage = "results"
                st.rerun()


# =====================
# RESULTS SCREEN
# =====================
elif st.session_state.stage == "results":
    results = st.session_state.results
    summary = st.session_state.summary

    st.markdown(f"""
    <div class="geab-header">
        <div>
            <h1>Assessment Complete</h1>
            <div class="subtitle">Candidate: {st.session_state.candidate_name}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.time_up:
        st.warning("Time expired. Your answers have been submitted automatically.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tier = summary["assessed_tier"]
        st.markdown(f"""
        <div class="score-card">
            <div class="big-score">{summary['total_scored']} / {summary['total_possible']}</div>
            <div class="tier-label">Assessed Level: {tier_badge_html(tier)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Question Breakdown")

    for r in results:
        if r["points_awarded"] == r["points_possible"]:
            css = "feedback-correct"
            icon = "\u2705"
        elif r["points_awarded"] > 0:
            css = "feedback-partial"
            icon = "\U0001F7E1"
        else:
            css = "feedback-wrong"
            icon = "\u274C"

        st.markdown(f"""
        <div class="{css}">
            <strong>{icon} Q{r['question_id']}. {r['title']}</strong> &nbsp; {tier_badge_html(r['tier'])}
            <br/>
            <strong>{r['points_awarded']}/{r['points_possible']} points</strong> &mdash; {r['feedback']}
        </div>
        """, unsafe_allow_html=True)

        answer = st.session_state.answers.get(r["question_id"], "")
        if answer.strip():
            with st.expander(f"View submitted SQL for Q{r['question_id']}"):
                st.code(answer, language="sql")
        st.markdown("")

    st.markdown("---")
    st.caption(f"Submitted at {datetime.now().strftime('%d %B %Y, %H:%M')}. Results saved to submissions folder.")
