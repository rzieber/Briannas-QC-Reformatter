import re
import ast
import csv
import pandas as pd
from pathlib import Path

"""
Takes observations stored in JSON-lines style daily files and converts them to a single csv.

Requirements: 
    - data_origin and data_destination folder paths
    - file_name specified (file exension included)
    - assumes final timestamp column is named 'time'
        * assumes that the timestamp column is named 'at' by default, which gets renamed at the end to 'time'
    - assumes that files contain the .log extension
    
"""

data_origin = Path("")
data_destination = Path("")
file_name = ""
data_destination.mkdir(parents=True, exist_ok=True)

def parse_line(s: str):
    s = s.strip()
    
    if not s: return None

    s = re.sub(r',\s*([}\]])', r'\1', s)
    try:
        obj = ast.literal_eval(s)   # handles single quotes, floats, etc.
        return dict(obj) if isinstance(obj, dict) else None
    except Exception:
        return None

all_dfs = []
headers = []                        # order-preserving list of keys
seen = set()                        # to track what's been added to headers

for log in data_origin.rglob("*.log"):
    print(log.name)

    rows = []
    with open(log, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            rec = parse_line(line)
            if rec is None:
                continue
            rows.append(rec)
            
            for k in rec.keys():    # update headers in first-seen order
                if k not in seen:
                    headers.append(k)
                    seen.add(k)

    if not rows:
        continue

    df = pd.DataFrame(rows)
    df = df.reindex(columns=headers)

    if 'at' in df.columns:
        df['at'] = pd.to_datetime(df['at'], errors='coerce')
        df.rename(columns={'at':'time'}, inplace=True)

    all_dfs.append(df)

if all_dfs:
    csv = pd.concat(all_dfs, axis=0, ignore_index=True)
    csv.sort_values(by='time', inplace=True)
else:
    csv = pd.DataFrame(columns=headers)

csv.to_csv(data_destination / file_name, index=False)
