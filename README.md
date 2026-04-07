# GEAB SQL Assessment

A Streamlit app for assessing SQL skills as part of the RevOps Analyst hiring process.

## Quick Start
```bash
pip install -r requirements.txt
python seed_db.py
streamlit run app.py
```

## Scoring

| Tier | Questions | Points | Cumulative | Skills Tested |
|------|-----------|--------|-----------|---------------|
| Foundation | Q1-Q3 | 3 | 0-3 | SELECT, WHERE, ORDER BY, simple JOINs |
| Intermediate | Q4-Q5 | 5 | 4-8 | Multi-table JOINs, GROUP BY, HAVING, dates |
| Advanced | Q6-Q7 | 8 | 9-16 | Subqueries, date arithmetic, revenue calcs |
| Expert | Q8 | 5 | 17-21 | CTEs, window functions, RANK, tie handling |

Total: 21 points. Partial credit awarded for sound logic.

## Deploy to Streamlit Cloud (Free)

1. Push to GitHub (keep repo **private**, it contains answer keys)
2. Go to share.streamlit.io
3. Connect GitHub, select repo, set `app.py` as main file
4. Deploy (database auto-seeds on first run)

## Submissions

Saved as JSON in `submissions/` with candidate name, answers, scores, and tier.
