"""
Seed a SQLite database with video shop test data.
Run once before launching the Streamlit app.
"""

import sqlite3
import os
import random
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "videoshop.db")

def seed():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE Customer (
            Cust_Id INTEGER PRIMARY KEY,
            Membership_No TEXT NOT NULL,
            Joined_Date DATE NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE Contact (
            Contact_Id INTEGER PRIMARY KEY,
            Full_Name TEXT NOT NULL,
            Address_Id INTEGER NOT NULL,
            Phone_Number TEXT,
            Cust_Id INTEGER NOT NULL,
            Created_Date DATE NOT NULL,
            FOREIGN KEY (Cust_Id) REFERENCES Customer(Cust_Id),
            FOREIGN KEY (Address_Id) REFERENCES Address(Address_Id)
        )
    """)
    c.execute("""
        CREATE TABLE Address (
            Address_Id INTEGER PRIMARY KEY,
            Address_Line_1 TEXT NOT NULL,
            Postcode TEXT NOT NULL,
            Contact_Id INTEGER,
            FOREIGN KEY (Contact_Id) REFERENCES Contact(Contact_Id)
        )
    """)
    c.execute("""
        CREATE TABLE Rental_History (
            History_Id INTEGER PRIMARY KEY,
            Video_Id INTEGER NOT NULL,
            Rental_Start_Date DATE NOT NULL,
            Rental_End_Date DATE,
            Cust_Id INTEGER NOT NULL,
            FOREIGN KEY (Video_Id) REFERENCES Videos(Video_Id),
            FOREIGN KEY (Cust_Id) REFERENCES Customer(Cust_Id)
        )
    """)
    c.execute("""
        CREATE TABLE Videos (
            Video_Id INTEGER PRIMARY KEY,
            Film_Name TEXT NOT NULL,
            Genre TEXT NOT NULL,
            Release_Year INTEGER NOT NULL,
            Daily_Rate REAL NOT NULL
        )
    """)

    videos = [
        (1, "The Shawshank Redemption", "Drama", 1994, 2.50),
        (2, "Pulp Fiction", "Crime", 1994, 3.00),
        (3, "The Exorcist", "Horror", 1973, 2.00),
        (4, "Scream", "Horror", 1996, 3.50),
        (5, "Toy Story", "Animation", 1995, 2.00),
        (6, "Die Hard", "Action", 1988, 2.50),
        (7, "Goodfellas", "Crime", 1990, 3.00),
        (8, "The Silence of the Lambs", "Horror", 1991, 2.75),
        (9, "Forrest Gump", "Drama", 1994, 2.50),
        (10, "Jurassic Park", "Action", 1993, 3.50),
        (11, "The Lion King", "Animation", 1994, 1.50),
        (12, "Se7en", "Crime", 1995, 3.00),
        (13, "Braveheart", "Drama", 1995, 2.50),
        (14, "Halloween", "Horror", 1978, 2.00),
        (15, "Speed", "Action", 1994, 2.75),
    ]
    c.executemany("INSERT INTO Videos VALUES (?,?,?,?,?)", videos)

    names = [
        "Alice Brown", "Ben Carter", "Charlie Davies", "Diana Evans",
        "Edward Fisher", "Fiona Green", "George Harris", "Hannah Irving",
        "Ian Jones", "Julia King", "Karl Lewis", "Laura Mitchell",
        "Michael Norton", "Natalie Owen", "Oliver Parker", "Patricia Quinn",
        "Robert Smith", "Sarah Taylor", "Thomas Underwood", "Victoria Ward",
    ]

    postcodes = [
        "RG40 2DB", "RG40 2DB", "RG40 3AB", "RG40 1XY",
        "RG41 2QP", "RG40 5TT", "RG41 1AA", "RG40 2DB",
        "SN1 4BD", "SN1 4BD", "RG40 7HH", "OX1 3DP",
        "OX1 3DP", "RG40 2DB", "SN1 9XZ", "RG40 3AB",
        "RG41 2QP", "BS1 5AA", "BS1 5AA", "RG40 1XY",
    ]

    streets = [
        "12 High Street", "45 Station Road", "78 Church Lane", "3 Park Avenue",
        "22 Mill Road", "99 The Green", "17 King Street", "50 London Road",
        "8 Victoria Terrace", "31 Queens Drive", "64 Oak Lane", "11 Broad Street",
        "27 Castle Road", "5 Elm Close", "40 River Walk", "15 North Street",
        "88 South Parade", "2 West End", "66 East Row", "33 Bridge Lane",
    ]

    join_base = date(2021, 1, 5)
    random.seed(42)

    for i, name in enumerate(names):
        cust_id = i + 1
        membership = f"MEM{1000 + cust_id}"
        joined = join_base + timedelta(days=random.randint(0, 1400))

        c.execute("INSERT INTO Customer VALUES (?,?,?)", (cust_id, membership, joined.isoformat()))
        c.execute("INSERT INTO Address VALUES (?,?,?,?)", (cust_id, streets[i], postcodes[i], cust_id))
        c.execute("INSERT INTO Contact VALUES (?,?,?,?,?,?)", (
            cust_id, name, cust_id, f"07700 {900000 + cust_id}", cust_id, joined.isoformat()
        ))

    random.seed(99)
    history_id = 1
    rental_data = []

    for cust_id in range(1, 21):
        num_rentals = random.randint(3, 15)
        for _ in range(num_rentals):
            video_id = random.randint(1, 15)
            start = date(2024, 1, 1) + timedelta(days=random.randint(0, 500))
            duration = random.randint(1, 14)
            if random.random() < 0.1:
                end = None
            else:
                end = (start + timedelta(days=duration)).isoformat()

            rental_data.append((history_id, video_id, start.isoformat(), end, cust_id))
            history_id += 1

    for cust_id in [1, 2, 3, 4, 6, 8, 11, 14, 16, 20]:
        for _ in range(2):
            video_id = random.randint(1, 15)
            day = random.randint(1, 31)
            if day > 28:
                day = 28
            start = date(2025, 3, day)
            duration = random.randint(1, 7)
            end = (start + timedelta(days=duration)).isoformat()
            rental_data.append((history_id, video_id, start.isoformat(), end, cust_id))
            history_id += 1

    c.executemany("INSERT INTO Rental_History VALUES (?,?,?,?,?)", rental_data)

    conn.commit()
    conn.close()
    print(f"Database seeded at {DB_PATH} with {len(rental_data)} rentals across {len(names)} customers.")


def ensure_db():
    """Seed the database if it doesn't exist. Safe to call on every app start."""
    if not os.path.exists(DB_PATH):
        seed()


if __name__ == "__main__":
    seed()
