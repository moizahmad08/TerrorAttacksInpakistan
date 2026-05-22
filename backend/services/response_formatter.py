"""Format agent / fallback chat responses."""

from typing import List, Tuple, Optional


def _describe_incident(doc: dict) -> str:
    location = doc.get("location", "Unknown")
    province = doc.get("province", "")
    place = f"{location}, {province}" if province else location
    deaths = doc.get("deaths", 0)
    injuries = doc.get("injuries", 0)
    desc = (doc.get("description") or "").strip()
    if len(desc) > 220:
        desc = desc[:217].rstrip() + "..."
    return (
        f"On **{doc.get('date', 'N/A')}**, at **{place}**, a **{doc.get('attack_type', 'attack')}** "
        f"targeted **{doc.get('target', 'unknown targets')}**. "
        f"**{doc.get('perpetrator', 'Unknown')}** was linked to the incident. "
        f"Reported casualties: **{deaths}** killed and **{injuries}** injured. "
        f"{desc}"
    ).strip()


def format_incidents_markdown(
    retrieved: List[Tuple[dict, float]],
    query: str,
    *,
    intro: Optional[str] = None,
) -> str:
    if not retrieved:
        return (
            "## No matching records\n\n"
            "I searched the database but could not find incidents matching your question.\n\n"
            "**Try asking about:**\n"
            "- A city (Peshawar, Karachi, Quetta, Lahore)\n"
            "- A year (e.g. 2014, 2023)\n"
            "- A group (TTP, ISKP, BLA)\n"
            "- A specific event (e.g. Peshawar school attack 2014)"
        )

    lines = [
        intro or f"## Summary\n\nFound **{len(retrieved)}** relevant incident(s) for your question.",
        "",
        "## Incidents",
        "",
    ]

    for i, (doc, _) in enumerate(retrieved, 1):
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
        "## Answer",
        "",
        f"I searched the full database. It contains **{total:,}** documented incidents "
        f"with **{deaths:,}** reported deaths and **{injuries:,}** injuries "
        f"(about **{avg}** deaths per incident on average).",
        "",
        "### Top provinces",
        "",
    ]
    for name, count in top_provinces:
        lines.append(f"- **{name}:** {count} incidents")

    lines.extend(["", "### Most active groups", ""])
    for name, count in top_groups:
        short = name if len(name) <= 48 else name[:45] + "..."
        lines.append(f"- **{short}:** {count} incidents")

    lines.extend([
        "",
        "## Note",
        "",
        "Ask about a specific city, year, or attack for a detailed incident brief.",
    ])
    return "\n".join(lines)


def format_agent_fallback(
    query: str,
    retrieved: List[Tuple[dict, float]],
    stats: Optional[dict] = None,
    intent: str = "general",
) -> str:
    """
    Database-only agent: search results + natural-language summary (no Grok API).
    """
    if intent == "statistics" and stats:
        return format_statistics_markdown(stats, query)

    if not retrieved:
        return format_incidents_markdown([], query)

    docs = [doc for doc, _ in retrieved]

    if len(docs) == 1:
        summary = (
            "## Answer\n\n"
            "I searched the database and found one matching incident:\n\n"
            + _describe_incident(docs[0])
        )
    else:
        top = docs[0]
        summary = (
            "## Answer\n\n"
            f"I searched the database and found **{len(docs)}** related incidents. "
            f"The closest match is the **{top.get('date')}** attack in **{top.get('location')}** "
            f"({top.get('province')}) — **{top.get('deaths')}** killed, "
            f"attributed to **{top.get('perpetrator', 'unknown')}**.\n\n"
            "See the records below for full details."
        )

    records = format_incidents_markdown(
        retrieved,
        query,
        intro="## Matching records from database",
    )
    return f"{summary}\n\n{records}"
