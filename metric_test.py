

from data.cache import get_connection
conn = get_connection()
conn.row_factory = __import__('sqlite3').Row
rows = conn.execute("""
    SELECT model, brand, dry_braking, dry_handling, wet_braking
    FROM tire_results
    WHERE test_name = '2022/23 Tyre Reviews 17 Inch Summer Tyre Test'
    AND tire_size = '225/45 R17'
""").fetchall()
for r in rows:
    print(dict(r))
conn.close()