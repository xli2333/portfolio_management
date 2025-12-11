import os
import csv
import time
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# 1. Connect to Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

supabase = create_client(url, key)

# 2. Read CSV
csv_path = "A share names.csv"
if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found.")
    exit(1)

print("Reading CSV...")
rows_to_insert = []
try:
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        # Normalize headers
        if reader.fieldnames:
            reader.fieldnames = [name.strip() for name in reader.fieldnames]
            
        for row in reader:
            raw_code = row.get('证券代码')
            name = row.get('证券名称')
            
            if raw_code and name:
                code = raw_code.strip().split('.')[0]
                clean_name = name.strip()
                
                rows_to_insert.append({
                    "symbol": code,
                    "name": clean_name,
                    "market": "CN"
                })
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit(1)

print(f"Found {len(rows_to_insert)} records.")

# 3. Upload to Supabase (Batch)
BATCH_SIZE = 1000
table = "stock_metadata"

print("Starting upload to Supabase...")
for i in range(0, len(rows_to_insert), BATCH_SIZE):
    batch = rows_to_insert[i : i + BATCH_SIZE]
    try:
        # upsert=True is implicit if we rely on Primary Key (symbol) conflict resolution?
        # Supabase-py 'upsert' method:
        response = supabase.table(table).upsert(batch).execute()
        print(f"Uploaded batch {i} - {i+len(batch)}")
        time.sleep(0.5) # Rate limit protection
    except Exception as e:
        print(f"Error uploading batch {i}: {e}")

print("Upload complete!")
