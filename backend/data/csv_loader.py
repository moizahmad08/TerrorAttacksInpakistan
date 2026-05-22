"""Load attack records from project CSV files."""

import csv
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent
BACKEND_DIR = DATA_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

# Primary merged dataset (Supabase schema: new_id, source, ...)
COMBINED_PATHS = [
    BACKEND_DIR / "combined_incidents.csv",  # Docker: mounted at /app/
    ROOT_DIR / "combined_incidents.csv",     # Local dev: project root
    DATA_DIR / "combined_incidents.csv",
]

# Legacy fallbacks if combined file missing
LEGACY_INCIDENTS_PATHS = [
    DATA_DIR / "pakistan_incidents_1947_2026.csv",
    ROOT_DIR / "pakistan_incidents_1947_2026.csv",
]
LEGACY_ATTACKS_CSV = DATA_DIR / "attacks.csv"


def _find_combined_csv():
    for path in COMBINED_PATHS:
        if path.exists():
            return path
    # combined_incidents/ folder with any single .csv inside
    for folder in (ROOT_DIR / "combined_incidents", BACKEND_DIR / "combined_incidents"):
        if folder.is_dir():
            csvs = sorted(folder.glob("*.csv"))
            if csvs:
                return csvs[0]
    return None


def _find_legacy_incidents_csv():
    for path in LEGACY_INCIDENTS_PATHS:
        if path.exists():
            return path
    return None


def parse_date(value: str) -> str:
    """Normalize dates from ISO (1947-10-07) or US (10/7/1947) formats."""
    s = (value or "").strip()
    if not s:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%d/%m/%Y"):
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


def parse_attack_date(raw: str):
    """Parse attacks.csv style: Sunday-November 19-1995"""
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


def pick_int(*values):
    for v in values:
        n = safe_int(v, default=-1)
        if n >= 0:
            return n
    return 0


def _row_to_attack(row: dict, default_source: str = "CSV") -> dict:
    """Map a combined_incidents / Supabase-style CSV row to app format."""
    date_iso = parse_date(row.get("date", ""))
    killed = safe_int(row.get("killed"))
    wounded = safe_int(row.get("wounded"))
    record_id = (row.get("new_id") or row.get("incident_id") or "").strip()

    return {
        "id": record_id,
        "date": date_iso,
        "location": (row.get("city") or "").strip(),
        "province": (row.get("region") or "").strip(),
        "attack_type": (row.get("attack_type") or "").strip(),
        "target": (row.get("target_type") or "").strip(),
        "perpetrator": (row.get("perpetrator_group") or "Unknown").strip() or "Unknown",
        "deaths": killed,
        "injuries": wounded,
        "description": (row.get("notes") or "").strip(),
        "source": (row.get("source") or default_source).strip() or default_source,
    }


def load_combined_records() -> list:
    path = _find_combined_csv()
    if not path:
        return []

    records = []
    seen_ids = set()

    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            record_id = (row.get("new_id") or row.get("incident_id") or "").strip()
            if not record_id or record_id in seen_ids:
                continue
            if not parse_date(row.get("date", "")):
                continue
            seen_ids.add(record_id)
            records.append(_row_to_attack(row, default_source=row.get("source", "CSV").strip() or "CSV"))

    return records


def load_legacy_records() -> list:
    """Load older split CSV files only if combined_incidents.csv is missing."""
    records = []
    seen_ids = set()

    incidents_path = _find_legacy_incidents_csv()
    if incidents_path:
        with open(incidents_path, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                record_id = row.get("incident_id", "").strip()
                if not record_id or record_id in seen_ids:
                    continue
                seen_ids.add(record_id)
                row["new_id"] = record_id
                records.append(_row_to_attack(row, default_source="PAK"))

    if LEGACY_ATTACKS_CSV.exists():
        with open(LEGACY_ATTACKS_CSV, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                parsed = parse_attack_date(row.get("Date", ""))
                if not parsed:
                    continue
                record_id = f"ATK-{row.get('S#', '').strip().zfill(4)}"
                if record_id in seen_ids:
                    continue
                seen_ids.add(record_id)

                location = (row.get("Location") or "").strip()
                city = (row.get("City") or "").strip()
                province = (row.get("Province") or "").strip()
                target = (row.get("Target Type") or "").strip()
                suicide = safe_int(row.get("No. of Suicide Blasts"))
                attack_type = "Suicide bombing" if suicide > 0 else "Bombing / IED"

                records.append({
                    "id": record_id,
                    "date": parsed.isoformat(),
                    "location": city or location,
                    "province": province,
                    "attack_type": attack_type,
                    "target": target or "Unknown",
                    "perpetrator": "Unknown",
                    "deaths": pick_int(row.get("Killed Max"), row.get("Killed Min")),
                    "injuries": pick_int(row.get("Injured Max"), row.get("Injured Min")),
                    "description": (row.get("Location") or "") + " " + (row.get("Target Type") or ""),
                    "source": row.get("source", "ATK").strip() or "ATK",
                })

    return records


def load_all_records() -> list:
    """Prefer combined_incidents.csv; fall back to legacy CSV pair."""
    combined = load_combined_records()
    if combined:
        return combined
    return load_legacy_records()
