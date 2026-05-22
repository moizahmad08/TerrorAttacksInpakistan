"""
Import incident data into Supabase databaseterrorattacks table.

Primary source: combined_incidents.csv (project root)
"""

import csv
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]


def _resolve_combined_csv() -> Path:
    candidates = [
        ROOT / "combined_incidents.csv",
        ROOT / "combined_incidents" / "combined_incidents.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    folder = ROOT / "combined_incidents"
    if folder.is_dir():
        csvs = sorted(folder.glob("*.csv"))
        if csvs:
            return csvs[0]
    return ROOT / "combined_incidents.csv"
TABLE = "databaseterrorattacks"
BATCH_SIZE = 200


def parse_date(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s.split()[0], fmt).date().isoformat()
        except ValueError:
            continue
    return s


def safe_int(value, default=0):
    if value is None or str(value).strip() in ("", "NA", "N/A", "na"):
        return default
    try:
        return int(float(str(value).strip().replace(",", "")))
    except (ValueError, TypeError):
        return default


def load_combined_rows():
    combined_csv = _resolve_combined_csv()
    if not combined_csv.exists():
        logger.error("Missing combined incidents file. Expected: %s", combined_csv)
        sys.exit(1)

    rows = []
    with open(combined_csv, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            new_id = (row.get("new_id") or row.get("incident_id") or "").strip()
            if not new_id:
                continue
            date_iso = parse_date(row.get("date", ""))
            if not date_iso:
                logger.warning("Skipping row with bad date: %s %s", new_id, row.get("date"))
                continue

            killed = safe_int(row.get("killed"))
            wounded = safe_int(row.get("wounded"))
            try:
                y, m, d = date_iso.split("-")
                year, month, day = int(y), int(m), int(d)
            except ValueError:
                year = safe_int(row.get("year"))
                month = safe_int(row.get("month"))
                day = safe_int(row.get("day"))

            rows.append({
                "new_id": new_id,
                "source": (row.get("source") or "Unknown").strip() or "Unknown",
                "date": date_iso,
                "year": year,
                "month": month,
                "day": day,
                "country": row.get("country", "Pakistan").strip() or "Pakistan",
                "region": row.get("region", "").strip(),
                "city": row.get("city", "").strip(),
                "attack_type": row.get("attack_type", "").strip(),
                "target_type": row.get("target_type", "").strip(),
                "perpetrator_group": row.get("perpetrator_group", "Unknown").strip() or "Unknown",
                "killed": killed,
                "wounded": wounded,
                "total_casualties": safe_int(row.get("total_casualties"), killed + wounded),
                "attack_success": row.get("attack_success", "Yes").strip() or "Yes",
                "property_damage": row.get("property_damage", "Unknown").strip() or "Unknown",
                "notes": row.get("notes", "").strip(),
            })
    return rows


def upsert_batches(supabase, records):
    total = 0
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]
        supabase.table(TABLE).upsert(batch, on_conflict="new_id").execute()
        total += len(batch)
        logger.info("Upserted %s / %s records", total, len(records))
    return total


def main():
    load_dotenv(ROOT / "backend" / ".env")
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set in backend/.env")
        sys.exit(1)

    records = load_combined_rows()
    combined_csv = _resolve_combined_csv()
    logger.info("Loaded %s rows from %s", len(records), combined_csv)

    supabase = create_client(url, key)

    before = supabase.table(TABLE).select("new_id", count="exact").limit(1).execute()
    logger.info("Rows in Supabase before import: %s", before.count)

    upsert_batches(supabase, records)

    after = supabase.table(TABLE).select("new_id", count="exact").limit(1).execute()
    logger.info("Rows in Supabase after import: %s", after.count)
    logger.info("Import complete.")


if __name__ == "__main__":
    main()
