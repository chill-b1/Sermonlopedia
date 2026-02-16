import json
import psycopg2

# --- 1. Load JSON data from file ---
with open("tscript.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

# --- 2. Connect to PostgreSQL ---
conn = psycopg2.connect(
    dbname="your_db_name",
    user="your_username",
    password="your_password",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

table_name = "sermon_segments"

# --- 3. Build columns dynamically based on JSON keys ---
columns = []
for key, value in json_data.items():
    if key == "transcript":
        col_type = "JSONB"
    elif isinstance(value, int):
        col_type = "INTEGER"
    elif isinstance(value, float):
        col_type = "REAL"
    elif isinstance(value, bool):
        col_type = "BOOLEAN"
    else:
        col_type = "TEXT"
    columns.append(f"{key} {col_type}")

# --- 4. Create table if it doesn’t exist ---
create_table_query = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    id SERIAL PRIMARY KEY,
    {', '.join(columns)}
);
"""
cur.execute(create_table_query)

# --- 5. Insert JSON data ---
keys = json_data.keys()
values = [json.dumps(v) if isinstance(v, dict) else v for v in json_data.values()]
placeholders = ', '.join(['%s'] * len(values))

insert_query = f"""
INSERT INTO {table_name} ({', '.join(keys)})
VALUES ({placeholders});
"""
cur.execute(insert_query, values)

# --- 6. Commit and close ---
conn.commit()
cur.close()
conn.close()
