"""Format RAG / fallback chat responses as structured markdown."""

from typing import List, Tuple


def format_incidents_markdown(
    retrieved: List[Tuple[dict, float]],
    query: str,
    *,
    intro: str | None = None,
) -> str:
    if not retrieved:
        return (
            "## No matching records\n\n"
            "I could not find incidents in the database that match your question.\n\n"
            "**Try asking about:**\n"
            "- A city (Peshawar, Karachi, Quetta, Lahore)\n"
            "- A year (e.g. 2014, 2023)\n"
            "- A group (TTP, ISKP, BLA)\n"
            "- A type of attack (suicide bombing, school attack)"
        )

    lines = [
        intro or f"## Summary\n\nFound **{len(retrieved)}** relevant incident(s) in the knowledge base for your query.",
        "",
        "## Incidents",
        "",
    ]

    for i, (doc, score) in enumerate(retrieved, 1):
        location = doc.get("location", "Unknown")
        province = doc.get("province", "")
        place = f"{location}, {province}" if province else location
        deaths = doc.get("deaths", 0)
        injuries = doc.get("injuries", 0)
        desc = (doc.get("description") or "").strip()
        if len(desc) > 280:
            desc = desc[:277].rstrip() + "..."

        lines.extend([
            f"### {i}. {place} — {doc.get('date', 'N/A')}",
            "",
            f"- **Attack type:** {doc.get('attack_type', 'Unknown')}",
            f"- **Target:** {doc.get('target', 'Unknown')}",
            f"- **Perpetrator:** {doc.get('perpetrator', 'Unknown')}",
            f"- **Casualties:** **{deaths}** killed, **{injuries}** injured",
            f"- **Details:** {desc}" if desc else "",
            f"- **Source:** {doc.get('source', 'Database')}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "*Figures are from official or reported sources in the database. "
        "Add `GROK_API_KEY` in `.env` for natural-language analysis beyond these records.*",
    ])
    return "\n".join(line for line in lines if line is not None)


def format_statistics_markdown(stats: dict, query: str) -> str:
    total = stats.get("total_incidents", 0)
    deaths = stats.get("total_deaths", 0)
    injuries = stats.get("total_injuries", 0)
    avg = round(deaths / total) if total else 0

    top_provinces = sorted(
        stats.get("by_province", {}).items(), key=lambda x: x[1], reverse=True
    )[:5]
    top_groups = sorted(
        stats.get("by_perpetrator", {}).items(), key=lambda x: x[1], reverse=True
    )[:5]

    lines = [
        "## Database statistics",
        "",
        f"The knowledge base contains **{total:,}** documented incidents.",
        "",
        "### Overview",
        "",
        f"- **Total deaths (reported):** {deaths:,}",
        f"- **Total injuries (reported):** {injuries:,}",
        f"- **Average deaths per incident:** {avg}",
        "",
        "### Top provinces by incident count",
        "",
    ]
    for name, count in top_provinces:
        lines.append(f"- **{name}:** {count} incidents")

    lines.extend(["", "### Most active perpetrator groups", ""])
    for name, count in top_groups:
        short = name if len(name) <= 48 else name[:45] + "..."
        lines.append(f"- **{short}:** {count} incidents")

    lines.extend([
        "",
        "---",
        "",
        "*Ask about a specific city, year, or group for detailed incident records.*",
    ])
    return "\n".join(lines)
