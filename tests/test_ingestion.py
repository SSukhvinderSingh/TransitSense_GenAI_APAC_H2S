#!/usr/bin/env python3
"""Tests for Data Ingestion Agent."""
import json
import os
import sqlite3
import sys
import tempfile
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ingest import validate_schema, scan_pii, ingest_file, SCHEMAS


def test_validate_schema_valid(tmp_path):
    csv_path = tmp_path / "test.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["route_id", "route_long_name", "agency_id", "route_type"])
        writer.writerow(["1", "Route 1", "TGSRTC", "3"])

    fields = validate_schema(str(csv_path), SCHEMAS["routes.csv"])
    assert "route_id" in fields
    assert "route_type" in fields


def test_validate_schema_missing_column(tmp_path):
    csv_path = tmp_path / "test.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["route_id", "route_long_name"])

    try:
        validate_schema(str(csv_path), SCHEMAS["routes.csv"])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Missing required column" in str(e)


def test_pii_scan():
    assert scan_pii("test@example.com") is True
    assert scan_pii("123456789012") is True
    assert scan_pii("9876543210") is True
    assert scan_pii("normal text") is False
    assert scan_pii("Charminar bus stop") is False


def test_ingest_file_creates_table_and_source_tag(tmp_path):
    csv_path = tmp_path / "test_routes.csv"
    db_path = tmp_path / "test.db"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["route_id", "route_long_name", "agency_id", "route_type"])
        writer.writerow(["1", "Route 1", "TGSRTC", "3"])
        writer.writerow(["2", "Route 2", "TGSRTC", "3"])

    conn = sqlite3.connect(str(db_path))
    schema = SCHEMAS["routes.csv"]
    report = {}
    ingest_file(conn, str(csv_path), schema, report)

    rows = conn.execute("SELECT * FROM routes ORDER BY route_id").fetchall()
    assert len(rows) == 2
    assert rows[0][0] == "1"
    assert rows[0][1] == "Route 1"

    conn.close()
    assert report["test_routes.csv"]["inserted_rows"] == 2
