from data.cache import get_connection

conn = get_connection()
count = conn.execute("SELECT COUNT(*) FROM tire_results").fetchone()[0]
sizes = conn.execute("SELECT COUNT(DISTINCT tire_size) FROM tire_results").fetchone()[0]
brands = conn.execute("SELECT COUNT(DISTINCT brand) FROM tire_results").fetchone()[0]
vehicles = conn.execute("SELECT COUNT(DISTINCT test_vehicle) FROM tire_results").fetchone()[0]

print(f"Total records: {count}")
print(f"Unique tire sizes: {sizes}")
print(f"Unique brands: {brands}")
print(f"Unique vehicles: {vehicles}")


cursor = conn.execute("SELECT * FROM tire_results LIMIT 1")
print([description[0] for description in cursor.description])

conn.close()