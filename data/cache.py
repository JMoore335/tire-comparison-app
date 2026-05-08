import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tires.db")

POPULAR_BRANDS = (
    "Michelin", "Bridgestone", "Goodyear", "Continental", "Pirelli",
    "Dunlop", "Hankook", "Yokohama", "Falken", "Kumho", "Toyo",
    "Nexen", "BFGoodrich", "Vredestein", "Maxxis", "Cooper",
    "Firestone", "Kleber", "Debica", "Semperit"
)


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
    print("Database initialized.")


def clear_db():
    """Wipe all data - useful when re-scraping fresh."""
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


def _brand_filter():
    """Return a SQL IN clause and params tuple for the popular brands filter."""
    placeholders = ",".join(["?" for _ in POPULAR_BRANDS])
    return f"AND brand IN ({placeholders})", tuple(POPULAR_BRANDS)


def query_by_size(tire_size: str) -> list[dict]:
    """Fetch popular brand tire results for a given size where test vehicle is known."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    brand_sql, brand_params = _brand_filter()

    cursor.execute(f"""
        SELECT * FROM tire_results
        WHERE LOWER(REPLACE(tire_size, ' ', '')) = LOWER(REPLACE(?, ' ', ''))
        AND test_vehicle IS NOT NULL
        {brand_sql}
        ORDER BY brand, test_year DESC
    """, (tire_size,) + brand_params)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_all_sizes() -> list[str]:
    """Return tire sizes that have at least one popular brand result."""
    conn = get_connection()
    cursor = conn.cursor()

    brand_sql, brand_params = _brand_filter()

    cursor.execute(f"""
        SELECT DISTINCT tire_size FROM tire_results
        WHERE test_vehicle IS NOT NULL
        {brand_sql}
        ORDER BY tire_size
    """, brand_params)

    sizes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sizes


def get_all_models() -> list[tuple]:
    """Return popular brand models that appeared in more than one test."""
    conn = get_connection()
    cursor = conn.cursor()

    brand_sql, brand_params = _brand_filter()

    cursor.execute(f"""
        SELECT brand, model
        FROM tire_results
        WHERE test_vehicle IS NOT NULL
        {brand_sql}
        GROUP BY brand, model
        HAVING COUNT(DISTINCT test_url) > 1
        ORDER BY brand, model
    """, brand_params)

    rows = cursor.fetchall()
    conn.close()
    return rows


def query_by_model(model: str) -> list[dict]:
    """
    Fetch all tires from tests where this model appeared.
    Only includes popular brands tested on the same vehicle with the same tire size.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    brand_sql, brand_params = _brand_filter()

    cursor.execute(f"""
        SELECT tr.*
        FROM tire_results tr
        INNER JOIN (
            SELECT DISTINCT test_url, tire_size, test_vehicle
            FROM tire_results
            WHERE model = ? AND test_vehicle IS NOT NULL
        ) target
        ON tr.test_url = target.test_url
        AND tr.tire_size = target.tire_size
        AND tr.test_vehicle = target.test_vehicle
        WHERE tr.test_vehicle IS NOT NULL
        {brand_sql}
        ORDER BY tr.test_url, tr.overall_rank ASC
    """, (model,) + brand_params)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows