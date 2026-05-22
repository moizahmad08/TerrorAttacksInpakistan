"""Load attack records from project CSV files."""

import csv
import re
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent
BACKEND_DIR = DATA_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

INCIDENTS_PATHS = [
    DATA_DIR / "pakistan_incidents_1947_2026.csv",
    ROOT_DIR / "pakistan_incidents_1947_2026.csv",
]
ATTACKS_CSV = DATA_DIR / "attacks.csv"


def _find_incidents_csv():
    for path in INCIDENTS_PATHS:
        if path.exists():
            return path
    return None


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


def load_all_records() -> list:
    """Load and merge CSV files into app attack record format."""
    records = []
    seen_ids = set()

    incidents_path = _find_incidents_csv()
    if incidents_path:
        with open(incidents_path, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                incident_id = row["incident_id"].strip()
                if incident_id in seen_ids:
                    continue
                seen_ids.add(incident_id)
                killed = safe_int(row.get("killed"))
                wounded = safe_int(row.get("wounded"))
                records.append({
                    "id": incident_id,
                    "date": row["date"].strip(),
                    "location": row.get("city", "").strip(),
                    "province": row.get("region", "").strip(),
                    "attack_type": row.get("attack_type", "").strip(),
                    "target": row.get("target_type", "").strip(),
                    "perpetrator": row.get("perpetrator_group", "Unknown").strip() or "Unknown",
                    "deaths": killed,
                    "injuries": wounded,
                    "description": row.get("notes", "").strip(),
                    "source": "CSV",
                })

    if ATTACKS_CSV.exists():
        with open(ATTACKS_CSV, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                parsed = parse_attack_date(row.get("Date", ""))
                if not parsed:
                    continue
                incident_id = f"ATK-{row.get('S#', '').strip().zfill(4)}"
                if incident_id in seen_ids:
                    continue
                seen_ids.add(incident_id)

                location = (row.get("Location") or "").strip()
                city = (row.get("City") or "").strip()
                province = (row.get("Province") or "").strip()
                target = (row.get("Target Type") or "").strip()
                sect = (row.get("Targeted Sect if any") or "").strip()
                event = (row.get("Influencing Event/Event") or "").strip()
                loc_cat = (row.get("Location Category") or "").strip()
                suicide = safe_int(row.get("No. of Suicide Blasts"))
                attack_type = "Suicide bombing" if suicide > 0 else "Bombing / IED"

                note_parts = [
                    f"Detailed blast record (S# {row.get('S#', '').strip()}).",
                    f"Location: {location}" if location else "",
                    f"Category: {loc_cat}" if loc_cat else "",
                    f"Target: {target}" if target else "",
                    f"Sect: {sect}" if sect and sect.lower() != "none" else "",
                    f"Context: {event}" if event else "",
                ]

                records.append({
                    "id": incident_id,
                    "date": parsed.isoformat(),
                    "location": city or location,
                    "province": province,
                    "attack_type": attack_type,
                    "target": target or loc_cat or "Unknown",
                    "perpetrator": "Unknown",
                    "deaths": pick_int(row.get("Killed Max"), row.get("Killed Min")),
                    "injuries": pick_int(row.get("Injured Max"), row.get("Injured Min")),
                    "description": " ".join(p for p in note_parts if p).strip(),
                    "source": "CSV",
                })

    return records
