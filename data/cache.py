import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tires.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Create the database and tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tire_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            test_url TEXT,
            test_year INTEGER,
            tire_size TEXT,
            test_vehicle TEXT,
            brand TEXT,
            model TEXT,
            wet_braking REAL,
            dry_braking REAL,
            wet_handling REAL,
            dry_handling REAL,
            subj_wet_handling REAL,
            subj_dry_handling REAL,
            straight_aquaplaning REAL,
            curved_aquaplaning REAL,
            noise_db REAL,
            subj_comfort REAL,
            overall_rank INTEGER,
            overall_score REAL,
            scraped_at TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialised.")

def clear_db():
    """Wipe all data — useful when re-scraping fresh."""
    conn = get_connection()
    conn.execute("DELETE FROM tire_results")
    conn.commit()
    conn.close()
    print("Database cleared.")

def insert_tire(data: dict):
    """Insert a single tire result into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tire_results (
            test_name, test_url, test_year, tire_size, test_vehicle,
            brand, model,
            wet_braking, dry_braking, wet_handling, dry_handling,
            subj_wet_handling, subj_dry_handling,
            straight_aquaplaning, curved_aquaplaning,
            noise_db, subj_comfort,
            overall_rank, overall_score, scraped_at
        ) VALUES (
            :test_name, :test_url, :test_year, :tire_size, :test_vehicle,
            :brand, :model,
            :wet_braking, :dry_braking, :wet_handling, :dry_handling,
            :subj_wet_handling, :subj_dry_handling,
            :straight_aquaplaning, :curved_aquaplaning,
            :noise_db, :subj_comfort,
            :overall_rank, :overall_score, :scraped_at
        )
    """, data)

    conn.commit()
    conn.close()

def query_by_size(tire_size: str) -> list[dict]:
    """Fetch all tire results for a given size where test vehicle is known."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM tire_results
        WHERE LOWER(REPLACE(tire_size, ' ', '')) = LOWER(REPLACE(?, ' ', ''))
        AND test_vehicle IS NOT NULL
        ORDER BY brand, test_year DESC
    """, (tire_size,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_all_sizes() -> list[str]:
    """Return a list of all tire sizes in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tire_size FROM tire_results ORDER BY tire_size")
    sizes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sizes