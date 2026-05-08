from data.cache import get_connection
import sqlite3

conn = get_connection()
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT test_vehicle, brand, model, tire_size, wet_braking, dry_braking, noise_db FROM tire_results").fetchall()
#rows = conn.execute("SELECT * FROM tire_results").fetchall()
for r in rows:
    print(dict(r))
conn.close()