"""Time entries export."""

from redmine_export import fmt_date_only, short_name


def export(client, project_id, config):
    """Export time entries for 04_activity.md."""
    print("  Fetching time entries...")

    def on_progress(fetched, total):
        print(f"\r  {fetched}/{total} time entries...", end="", flush=True)

    items = client.get_all(
        "/time_entries.json",
        "time_entries",
        params={"project_id": project_id},
        on_progress=on_progress,
    )

    if not items:
        return {}

    print(f"\r  -> {len(items)} time entries          ")
    lines = [f"\n# Time entries [{project_id}] ({len(items)})\n"]

    for t in items:
        date = fmt_date_only(t.get("spent_on", ""))
        user = short_name(t.get("user", {}).get("name", ""))
        issue = t.get("issue", {})
        issue_ref = f"ID:{issue['id']}" if issue else ""
        activity = t.get("activity", {}).get("name", "")
        hours = t.get("hours", 0)
        comment = t.get("comments", "")

        entry = f"[{date} {user} {issue_ref} {activity} {hours}h]"
        if comment:
            entry += f" \"{comment}\""
        lines.append(entry)

    lines.append("")
    return {"04_activity.md": "\n".join(lines)}
