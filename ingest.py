#!/usr/bin/env python3
"""
TransitSense Data Ingestion Agent.
Loads, validates, and normalizes raw transit CSVs into SQLite.
CLI: python ingest.py --input data/raw --output data/transitsense.db
"""
import argparse
import csv
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


PII_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"  # email
    r"|\b\d{12}\b"  # Aadhaar-like 12-digit
    r"|\b\d{10}\b"  # phone-like 10-digit
)


INGESTION_REPORT_PATH = "ingestion_report.json"

SCHEMAS = {
    "routes.csv": {
        "required": ["route_id", "route_long_name", "agency_id", "route_type"],
        "source": "real",
        "table": "routes",
        "columns": {
            "route_id": "TEXT PRIMARY KEY",
            "route_long_name": "TEXT",
            "agency_id": "TEXT",
            "route_type": "INTEGER",
        },
    },
    "stops.csv": {
        "required": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
        "source": "real",
        "table": "stops",
        "columns": {
            "stop_id": "TEXT PRIMARY KEY",
            "stop_name": "TEXT",
            "zone_id": "TEXT",
            "stop_lat": "REAL",
            "stop_lon": "REAL",
            "stop_desc": "TEXT",
        },
    },
    "trips_delays.csv": {
        "required": ["trip_id", "route_id", "date", "delay_minutes"],
        "source": "synthetic",
        "table": "trips_delays",
        "columns": {
            "trip_id": "TEXT",
            "route_id": "TEXT",
            "stop_id": "TEXT",
            "date": "TEXT",
            "scheduled_departure": "TEXT",
            "actual_departure": "TEXT",
            "delay_minutes": "REAL",
            "delay_reason": "TEXT",
            "_source": "TEXT",
        },
    },
    "ridership.csv": {
        "required": ["route_id", "date", "ridership_count"],
        "source": "synthetic",
        "table": "ridership",
        "columns": {
            "route_id": "TEXT",
            "date": "TEXT",
            "ridership_count": "INTEGER",
            "_source": "TEXT",
        },
    },
}


def validate_schema(filepath, schema_def):
    """Validate required columns exist. Returns fieldnames list or raises."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError(f"Empty file: {filepath}")
    header_stripped = [h.strip() for h in header]
    for req in schema_def["required"]:
        if req not in header_stripped:
            raise ValueError(
                f"Missing required column '{req}' in {os.path.basename(filepath)}. "
                f"Found columns: {header_stripped}"
            )
    return header_stripped


def scan_pii(value):
    """Returns True if PII pattern detected."""
    return bool(PII_PATTERN.search(str(value)))


def ingest_file(conn, filepath, schema_def, report):
    """Ingest a single CSV file into SQLite."""
    basename = os.path.basename(filepath)
    table = schema_def["table"]
    columns = schema_def["columns"]
    default_source = schema_def["source"]

    report[basename] = {"total_rows": 0, "inserted_rows": 0, "dropped_rows": [], "errors": []}

    fieldnames = validate_schema(filepath, schema_def)

    # Create table
    col_defs = ", ".join(f'"{col}" {dtype}' for col, dtype in columns.items())
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute(f"CREATE TABLE {table} ({col_defs})")

    # Build column index mapping
    col_index = {h: i for i, h in enumerate(fieldnames)}

    rows = []
    dropped = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row_num, row in enumerate(reader, start=2):
            report[basename]["total_rows"] += 1

            if not row or all(cell.strip() == "" for cell in row):
                continue

            record = {}
            valid = True
            errors = []

            for col in columns:
                if col in col_index:
                    val = row[col_index[col]].strip() if col_index[col] < len(row) else ""
                else:
                    val = ""

                if col == "_source" and not val:
                    val = default_source

                # PII scan on free-text columns
                if col in ("stop_desc", "delay_reason", "stop_name") and val:
                    if scan_pii(val):
                        errors.append(f"PII detected in column '{col}'")
                        valid = False

                record[col] = val

            if not valid:
                dropped.append({"row": row_num, "errors": errors})
                report[basename]["dropped_rows"].append(
                    {"row_number": row_num, "errors": errors, "raw_data": row}
                )
                continue

            for col, dtype in columns.items():
                val = record.get(col, "")
                if dtype == "REAL" and val:
                    try:
                        record[col] = float(val)
                    except ValueError:
                        record[col] = None
                elif dtype == "INTEGER" and val:
                    try:
                        record[col] = int(val)
                    except ValueError:
                        record[col] = None

            rows.append(tuple(record.get(c, "") for c in columns))

    # Batch insert
    if rows:
        placeholders = ", ".join(["?" for _ in columns])
        col_names = ", ".join(f'"{c}"' for c in columns)
        conn.executemany(
            f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", rows
        )
    conn.commit()

    INDEXES = {
        "trips_delays": [
            "CREATE INDEX IF NOT EXISTS idx_trips_delays_route_id ON trips_delays(route_id)",
            "CREATE INDEX IF NOT EXISTS idx_trips_delays_date ON trips_delays(date)",
        ],
        "ridership": [
            "CREATE INDEX IF NOT EXISTS idx_ridership_route_id ON ridership(route_id)",
        ],
        "stops": [
            "CREATE INDEX IF NOT EXISTS idx_stops_zone_id ON stops(zone_id)",
        ],
    }
    for stmt in INDEXES.get(table, []):
        conn.execute(stmt)
    conn.commit()

    report[basename]["inserted_rows"] = len(rows)

    if dropped:
        print(f"  Dropped {len(dropped)} row(s) from {basename}")
        for d in dropped:
            print(f"    Row {d['row']}: {'; '.join(d['errors'])}")


def main():
    parser = argparse.ArgumentParser(description="TransitSense Data Ingestion Agent")
    parser.add_argument("--input", default="data/raw", help="Input directory with CSV files")
    parser.add_argument("--output", default="data/transitsense.db", help="Output SQLite path")
    args = parser.parse_args()

    input_dir = args.input
    db_path = args.output

    print(f"TransitSense Data Ingestion Agent")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {db_path}")
    print()

    if not os.path.isdir(input_dir):
        print(f"Error: input directory '{input_dir}' not found")
        sys.exit(1)

    report = {"ingestion_date": datetime.utcnow().isoformat(), "input_dir": input_dir, "files": {}}

    conn = sqlite3.connect(db_path)

    for filename, schema_def in SCHEMAS.items():
        filepath = os.path.join(input_dir, filename)
        if not os.path.exists(filepath):
            report["files"][filename] = {"status": "skipped", "reason": f"File not found: {filepath}"}
            print(f"  Skipping {filename} — file not found")
            continue
        print(f"  Ingesting {filename}...")
        try:
            ingest_file(conn, filepath, schema_def, report["files"])
        except Exception as e:
            report["files"][filename] = {"status": "error", "error": str(e)}
            print(f"  Error ingesting {filename}: {e}")

    conn.close()

    # Write ingestion report
    report_path = os.path.join(os.path.dirname(db_path) or ".", INGESTION_REPORT_PATH)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Summary
    print()
    print("Ingestion complete. Summary:")
    for fname, fdata in report["files"].items():
        if "inserted_rows" in fdata:
            print(f"  {fname}: {fdata['inserted_rows']} rows inserted ({len(fdata['dropped_rows'])} dropped)")
        else:
            print(f"  {fname}: {fdata.get('status', 'unknown')}")

    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
