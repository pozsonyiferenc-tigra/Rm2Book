"""News export."""

from redmine_export import fmt_date, short_name


def export(client, project_id, config):
    """Export project news for 04_activity.md."""
    print("  Fetching news...")
    items = client.get_all(f"/projects/{project_id}/news.json", "news")

    if not items:
        return {}

    lines = [f"# News [{project_id}] ({len(items)})\n"]
    for n in items:
        author = short_name(n.get("author", {}).get("name", ""))
        date = fmt_date(n.get("created_on", ""))
        title = n.get("title", "")
        desc = n.get("description", "")
        lines.append(f"[{date} {author}] \"{title}\" {desc}")
        lines.append("")

    print(f"  -> {len(items)} news items")
    return {"04_activity.md": "\n".join(lines)}
