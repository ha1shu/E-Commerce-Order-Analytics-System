import sqlite3
import pandas as pd
import re
import os

SQL_FILE = "./sql_script/analysis_query.sql"
DB_FILE = "ecommerce.db"
OUTPUT_DIR = "query_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(SQL_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Split the file into blocks, each starting with a "-- N. Title" comment
# Pattern matches lines like: -- 1. Total revenue per category
pattern = re.compile(r"--\s*(\d+)\.\s*(.+)")
matches = list(pattern.finditer(content))

def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

conn = sqlite3.connect(DB_FILE)

for i, match in enumerate(matches):
    query_num = int(match.group(1))
    title = match.group(2)
    start = match.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
    query_sql = content[start:end].strip()

    if not query_sql:
        continue

    try:
        df = pd.read_sql_query(query_sql, conn)
        filename = f"q{query_num:02d}_{slugify(title)}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(filepath, index=False)
        print(f"Saved: {filename} ({len(df)} rows)")
    except Exception as e:
        print(f"ERROR in Query {query_num} ({title}): {e}")

conn.close()
print("\nDone. Check the 'query_results' folder.")