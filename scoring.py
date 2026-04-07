"""
Scoring engine: runs candidate SQL against the video shop database
and compares results to expected outputs.
"""

import sqlite3
import os
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "videoshop.db")

QUESTIONS = [
    {
        "id": 1,
        "title": "Customers with postcode RG40 2DB, alphabetical",
        "tier": "Foundation",
        "points": 1,
        "text": (
            "Write a query to return the **full name** and **phone number** of all customers "
            "with the postcode **'RG40 2DB'**, ordered alphabetically by name. "
            "Your result must contain exactly these two columns: Full_Name, Phone_Number."
        ),
        "hint": "You will need to join through Contact to reach the Address table.",
        "reference_sql": """
            SELECT co.Full_Name, co.Phone_Number
            FROM Contact co
            JOIN Address a ON co.Address_Id = a.Address_Id
            WHERE a.Postcode = 'RG40 2DB'
            ORDER BY co.Full_Name ASC
        """,
        "check_mode": "exact_ordered",
    },
    {
        "id": 2,
        "title": "Videos with daily rate > 2.50",
        "tier": "Foundation",
        "points": 1,
        "text": (
            "Write a query to return the **film name** and **genre** of all videos that have "
            "a daily rental rate of more than **2.50**, ordered by daily rate descending. "
            "Your result must contain exactly these two columns: Film_Name, Genre."
        ),
        "hint": "",
        "reference_sql": """
            SELECT Film_Name, Genre
            FROM Videos
            WHERE Daily_Rate > 2.50
            ORDER BY Daily_Rate DESC
        """,
        "check_mode": "exact_ordered",
    },
    {
        "id": 3,
        "title": "Total number of rentals",
        "tier": "Foundation",
        "points": 1,
        "text": "Write a query to count the **total number of rentals** recorded in the Rental_History table.",
        "hint": "",
        "reference_sql": "SELECT COUNT(*) FROM Rental_History",
        "check_mode": "value_match",
    },
    {
        "id": 4,
        "title": "March 2025 rentals for RG40 customers",
        "tier": "Intermediate",
        "points": 2,
        "text": (
            "Write a query to find all videos rented in **March 2025** by customers whose postcode "
            "starts with **'RG40'**. "
            "Your result must contain exactly these three columns: Full_Name, Film_Name, Rental_Start_Date."
        ),
        "hint": "Consider which tables you need to join and how dates are filtered.",
        "reference_sql": """
            SELECT co.Full_Name, v.Film_Name, rh.Rental_Start_Date
            FROM Rental_History rh
            JOIN Customer cu ON rh.Cust_Id = cu.Cust_Id
            JOIN Contact co ON cu.Cust_Id = co.Cust_Id
            JOIN Address a ON co.Address_Id = a.Address_Id
            JOIN Videos v ON rh.Video_Id = v.Video_Id
            WHERE rh.Rental_Start_Date >= '2025-03-01'
              AND rh.Rental_Start_Date < '2025-04-01'
              AND a.Postcode LIKE 'RG40%'
        """,
        "check_mode": "exact_set",
    },
    {
        "id": 5,
        "title": "Most popular genre by postcode (>5 rentals)",
        "tier": "Intermediate",
        "points": 3,
        "text": (
            "Write a query to find the **most popular video genre by postcode**. "
            "Only include postcodes with more than **5 total rentals**. "
            "Your result must contain exactly these three columns: Postcode, Genre, rental_count."
        ),
        "hint": "Think about how to group, count, and filter aggregated results.",
        "reference_sql": """
            SELECT a.Postcode, v.Genre, COUNT(*) as rental_count
            FROM Rental_History rh
            JOIN Customer cu ON rh.Cust_Id = cu.Cust_Id
            JOIN Contact co ON cu.Cust_Id = co.Cust_Id
            JOIN Address a ON co.Address_Id = a.Address_Id
            JOIN Videos v ON rh.Video_Id = v.Video_Id
            GROUP BY a.Postcode, v.Genre
            HAVING COUNT(*) > 5
            ORDER BY a.Postcode, rental_count DESC
        """,
        "check_mode": "exact_set",
    },
    {
        "id": 6,
        "title": "Total rental revenue per genre",
        "tier": "Advanced",
        "points": 4,
        "text": (
            "Write a query to calculate the **total rental revenue generated per genre**. "
            "Assume revenue equals the number of days rented multiplied by the video's daily rate. "
            "**Exclude** any rentals where the video has not yet been returned. "
            "Order by total revenue descending. "
            "Your result must contain exactly these two columns: Genre, total_revenue."
        ),
        "hint": "Revenue per rental = (Rental_End_Date - Rental_Start_Date) * Daily_Rate. A NULL Rental_End_Date means the video is still on loan.",
        "reference_sql": """
            SELECT v.Genre,
                   SUM((JULIANDAY(rh.Rental_End_Date) - JULIANDAY(rh.Rental_Start_Date)) * v.Daily_Rate) as total_revenue
            FROM Rental_History rh
            JOIN Videos v ON rh.Video_Id = v.Video_Id
            WHERE rh.Rental_End_Date IS NOT NULL
            GROUP BY v.Genre
            ORDER BY total_revenue DESC
        """,
        "check_mode": "exact_ordered",
    },
    {
        "id": 7,
        "title": "Customers above average rentals",
        "tier": "Advanced",
        "points": 4,
        "text": (
            "Write a query to find customers who have rented **more than the average number of "
            "rentals** across all customers. "
            "Your result must contain exactly these three columns: Full_Name, total_rentals, avg_rentals "
            "(rounded to 1 decimal place)."
        ),
        "hint": "You may use subqueries or CTEs.",
        "reference_sql": """
            SELECT co.Full_Name,
                   COUNT(*) as total_rentals,
                   ROUND((SELECT COUNT(*) * 1.0 / COUNT(DISTINCT Cust_Id) FROM Rental_History), 1) as avg_rentals
            FROM Rental_History rh
            JOIN Contact co ON rh.Cust_Id = co.Cust_Id
            GROUP BY rh.Cust_Id, co.Full_Name
            HAVING COUNT(*) > (SELECT COUNT(*) * 1.0 / COUNT(DISTINCT Cust_Id) FROM Rental_History)
        """,
        "check_mode": "exact_set",
    },
    {
        "id": 8,
        "title": "Each customer's top genre (with ties)",
        "tier": "Expert",
        "points": 5,
        "text": (
            "Write a query to identify each customer's **most frequently rented genre**. If a "
            "customer has a tie between genres, return **all tied genres**. "
            "Your result must contain exactly these three columns: Full_Name, Genre, rental_count."
        ),
        "hint": "This requires ranking genres per customer and handling ties. Consider using window functions such as RANK() or DENSE_RANK(), or a correlated subquery with MAX().",
        "reference_sql": """
            WITH genre_counts AS (
                SELECT rh.Cust_Id, v.Genre, COUNT(*) as cnt,
                       RANK() OVER (PARTITION BY rh.Cust_Id ORDER BY COUNT(*) DESC) as rnk
                FROM Rental_History rh
                JOIN Videos v ON rh.Video_Id = v.Video_Id
                GROUP BY rh.Cust_Id, v.Genre
            )
            SELECT co.Full_Name, gc.Genre, gc.cnt as rental_count
            FROM genre_counts gc
            JOIN Contact co ON gc.Cust_Id = co.Cust_Id
            WHERE gc.rnk = 1
        """,
        "check_mode": "exact_set",
    },
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def run_query(sql, conn=None):
    """Run a SQL query and return (columns, rows) or raise an exception."""
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
    finally:
        if own_conn:
            conn.close()


def normalise_rows(rows):
    """Convert all values to comparable strings, round floats."""
    result = []
    for row in rows:
        normalised = []
        for val in row:
            if val is None:
                normalised.append("NULL")
            elif isinstance(val, float):
                normalised.append(f"{val:.2f}")
            else:
                normalised.append(str(val).strip())
        result.append(tuple(normalised))
    return result


def score_answer(question, candidate_sql):
    """
    Score a candidate's SQL answer.
    Returns (points_awarded, max_points, feedback).
    """
    if not candidate_sql or not candidate_sql.strip():
        return 0, question["points"], "No answer provided."

    cleaned = candidate_sql.strip().rstrip(";").strip()
    if not re.match(r"(?i)^\s*(SELECT|WITH)\b", cleaned):
        return 0, question["points"], "Only SELECT queries (including CTEs) are allowed."

    dangerous = re.findall(r"\b(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)\b", cleaned, re.IGNORECASE)
    if dangerous:
        return 0, question["points"], f"Blocked keyword detected: {', '.join(dangerous)}. Only SELECT queries are allowed."

    conn = get_connection()
    try:
        ref_cols, ref_rows = run_query(question["reference_sql"], conn)
        ref_normalised = normalise_rows(ref_rows)

        try:
            cand_cols, cand_rows = run_query(cleaned, conn)
        except Exception as e:
            return 0, question["points"], f"SQL Error: {e}"

        cand_normalised = normalise_rows(cand_rows)

        mode = question["check_mode"]
        max_pts = question["points"]

        # Check column count mismatch upfront for clearer feedback
        if mode in ("exact_set", "exact_ordered") and len(cand_cols) != len(ref_cols):
            return 0, max_pts, (
                f"Column count mismatch: expected {len(ref_cols)} columns "
                f"({', '.join(ref_cols)}), got {len(cand_cols)} ({', '.join(cand_cols)})."
            )

        if mode == "value_match":
            if len(cand_rows) == 1 and len(cand_rows[0]) == 1:
                if cand_normalised[0][0] == ref_normalised[0][0]:
                    return max_pts, max_pts, "Correct!"
                else:
                    return 0, max_pts, f"Expected {ref_normalised[0][0]}, got {cand_normalised[0][0]}."
            else:
                return 0, max_pts, f"Expected a single value. Your query returned {len(cand_rows)} rows and {len(cand_cols)} columns."

        elif mode == "exact_ordered":
            if cand_normalised == ref_normalised:
                return max_pts, max_pts, "Correct! Results match perfectly including order."
            elif set(cand_normalised) == set(ref_normalised) and len(cand_normalised) == len(ref_normalised):
                return int(max_pts * 0.75), max_pts, "Correct data but ordering does not match. Partial credit awarded."
            else:
                correct_rows = set(cand_normalised) & set(ref_normalised)
                if len(correct_rows) > 0:
                    ratio = len(correct_rows) / len(ref_normalised)
                    partial = max(1, int(max_pts * ratio * 0.5))
                    partial = min(partial, max_pts - 1)
                    return partial, max_pts, (
                        f"Partial match: {len(correct_rows)}/{len(ref_normalised)} expected rows found. "
                        f"{len(cand_normalised) - len(correct_rows)} unexpected rows in your result."
                    )
                else:
                    return 0, max_pts, f"No matching rows. Expected {len(ref_normalised)} rows, got {len(cand_normalised)}."

        elif mode == "exact_set":
            cand_set = set(cand_normalised)
            ref_set = set(ref_normalised)
            if cand_set == ref_set:
                return max_pts, max_pts, "Correct! All rows match."
            else:
                correct = cand_set & ref_set
                missing = ref_set - cand_set
                extra = cand_set - ref_set
                if len(correct) > 0:
                    ratio = len(correct) / len(ref_set)
                    partial = max(1, int(max_pts * ratio * 0.6))
                    partial = min(partial, max_pts - 1)
                    feedback_parts = [f"{len(correct)}/{len(ref_set)} expected rows found."]
                    if missing:
                        feedback_parts.append(f"{len(missing)} rows missing.")
                    if extra:
                        feedback_parts.append(f"{len(extra)} unexpected rows.")
                    return partial, max_pts, " ".join(feedback_parts)
                else:
                    return 0, max_pts, f"No matching rows. Expected {len(ref_set)} rows, got {len(cand_set)}."

    finally:
        conn.close()

    return 0, question["points"], "Unable to score."


def score_all(answers: dict):
    """
    Score all answers.
    answers: dict of {question_id: sql_string}
    Returns list of result dicts and summary.
    """
    results = []
    total_scored = 0
    total_possible = 0

    for q in QUESTIONS:
        sql = answers.get(q["id"], "")
        scored, possible, feedback = score_answer(q, sql)
        total_scored += scored
        total_possible += possible
        results.append({
            "question_id": q["id"],
            "title": q["title"],
            "tier": q["tier"],
            "points_awarded": scored,
            "points_possible": possible,
            "feedback": feedback,
        })

    if total_scored >= 17:
        tier = "Expert"
    elif total_scored >= 9:
        tier = "Advanced"
    elif total_scored >= 4:
        tier = "Intermediate"
    else:
        tier = "Foundation"

    summary = {
        "total_scored": total_scored,
        "total_possible": total_possible,
        "assessed_tier": tier,
    }
    return results, summary
