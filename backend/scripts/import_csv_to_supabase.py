"""
Import all project CSV files into Supabase databaseterrorattacks table.

Sources:
  - pakistan_incidents_1947_2026.csv (root)
  - backend/data/attacks.csv
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
INCIDENTS_CSV = ROOT / "pakistan_incidents_1947_2026.csv"
ATTACKS_CSV = ROOT / "backend" / "data" / "attacks.csv"
TABLE = "databaseterrorattacks"
BATCH_SIZE = 200


def parse_attack_date(raw: str):
    s = (raw or "").strip()
    if not s:
        return None
    parts = s.split("-")
    if len(parts) < 3:
        return None
    try:
        year = int(parts[-1].strip())
    except ValueError:
        return None
    month_day = "-".join(parts[1:-1]).strip()
    if re.match(r"^[A-Za-z]{3,9}-\d{1,2}$", month_day):
        month_day = month_day.replace("-", " ")
    for fmt in ("%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(f"{month_day} {year}", fmt).date()
        except ValueError:
            pass
    return None


def safe_int(value, default=0):
    if value is None or str(value).strip() in ("", "NA", "N/A", "na"):
        return default
    try:
        return int(float(str(value).strip().replace(",", "")))
    except (ValueError, TypeError):
        return default


def pick_int(*values):
    for v in values:
        n = safe_int(v, default=-1)
        if n >= 0:
            return n
    return 0


def load_incidents_rows():
    rows = []
    with open(INCIDENTS_CSV, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            killed = safe_int(row.get("killed"))
            wounded = safe_int(row.get("wounded"))
            total = safe_int(row.get("total_casualties"), killed + wounded)
            rows.append(
                {
                    "new_id": row["incident_id"].strip(),
                    "date": row["date"].strip(),
                    "year": safe_int(row.get("year")),
                    "month": safe_int(row.get("month")),
                    "day": safe_int(row.get("day")),
                    "country": row.get("country", "Pakistan").strip() or "Pakistan",
                    "region": row.get("region", "").strip(),
                    "city": row.get("city", "").strip(),
                    "attack_type": row.get("attack_type", "").strip(),
                    "target_type": row.get("target_type", "").strip(),
                    "perpetrator_group": row.get("perpetrator_group", "Unknown").strip() or "Unknown",
                    "killed": killed,
                    "wounded": wounded,
                    "total_casualties": total,
                    "attack_success": row.get("attack_success", "Yes").strip() or "Yes",
                    "property_damage": row.get("property_damage", "Unknown").strip() or "Unknown",
                    "notes": row.get("notes", "").strip(),
                    "source": row.get("source", "CSV").strip() or "CSV",
                }
            )
    return rows


def load_attacks_rows():
    rows = []
    with open(ATTACKS_CSV, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            parsed = parse_attack_date(row.get("Date", ""))
            if not parsed:
                logger.warning("Skipping row with unparseable date: %s", row.get("Date"))
                continue

            killed = pick_int(row.get("Killed Max"), row.get("Killed Min"))
            wounded = pick_int(row.get("Injured Max"), row.get("Injured Min"))
            suicide = safe_int(row.get("No. of Suicide Blasts"))
            attack_type = "Suicide bombing" if suicide > 0 else "Bombing / IED"

            location = (row.get("Location") or "").strip()
            city = (row.get("City") or "").strip()
            province = (row.get("Province") or "").strip()
            target = (row.get("Target Type") or "").strip()
            sect = (row.get("Targeted Sect if any") or "").strip()
            event = (row.get("Influencing Event/Event") or "").strip()
            loc_cat = (row.get("Location Category") or "").strip()

            note_parts = [
                f"Detailed blast record from attacks.csv (S# {row.get('S#', '').strip()}).",
                f"Location: {location}" if location else "",
                f"Category: {loc_cat}" if loc_cat else "",
                f"Target: {target}" if target else "",
                f"Sect: {sect}" if sect and sect.lower() != "none" else "",
                f"Context: {event}" if event else "",
            ]
            notes = " ".join(p for p in note_parts if p).strip()

            rows.append(
                {
                    "new_id": f"ATK-{row.get('S#', '').strip().zfill(4)}",
                    "date": parsed.isoformat(),
                    "year": parsed.year,
                    "month": parsed.month,
                    "day": parsed.day,
                    "country": "Pakistan",
                    "region": province,
                    "city": city,
                    "attack_type": attack_type,
                    "target_type": target or loc_cat or "Unknown",
                    "perpetrator_group": "Unknown",
                    "killed": killed,
                    "wounded": wounded,
                    "total_casualties": killed + wounded,
                    "attack_success": "Yes",
                    "property_damage": "Unknown",
                    "notes": notes,
                    "source": row.get("source", "attacks.csv").strip() or "attacks.csv",
                }
            )
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

    if not INCIDENTS_CSV.exists():
        logger.error("Missing file: %s", INCIDENTS_CSV)
        sys.exit(1)
    if not ATTACKS_CSV.exists():
        logger.error("Missing file: %s", ATTACKS_CSV)
        sys.exit(1)

    incidents = load_incidents_rows()
    attacks = load_attacks_rows()
    all_records = incidents + attacks

    logger.info("Loaded %s incident rows and %s attack rows (%s total)", len(incidents), len(attacks), len(all_records))

    supabase = create_client(url, key)

    before = supabase.table(TABLE).select("new_id", count="exact").limit(1).execute()
    logger.info("Rows in Supabase before import: %s", before.count)

    upsert_batches(supabase, all_records)

    after = supabase.table(TABLE).select("new_id", count="exact").limit(1).execute()
    logger.info("Rows in Supabase after import: %s", after.count)
    logger.info("Import complete.")


if __name__ == "__main__":
    main()
