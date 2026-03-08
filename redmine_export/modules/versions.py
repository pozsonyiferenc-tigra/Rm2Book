"""Versions/milestones export."""

from redmine_export import fmt_date_only


def export(client, project_id, config):
    """Export project versions for 01_project_and_meta.md."""
    print("  Fetching versions...")
    data = client.get(f"/projects/{project_id}/versions.json")
    if not data or "versions" not in data:
        return {}

    versions = data["versions"]
    if not versions:
        return {}

    lines = ["\n## Versions\n"]
    for v in versions:
        name = v.get("name", "")
        status = v.get("status", "")
        due = fmt_date_only(v.get("due_date", ""))
        desc = v.get("description", "")

        parts = [name, status]
        if due:
            parts.append(f"Due:{due}")
        if desc:
            parts.append(f"\"{desc}\"")
        lines.append(" | ".join(parts))

    lines.append("")
    print(f"  -> {len(versions)} versions")
    return {"01_project_and_meta.md": "\n".join(lines)}
