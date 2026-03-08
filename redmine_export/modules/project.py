"""Project overview: info, members, trackers, statuses, priorities, categories."""

from redmine_export import fmt_date_only


def export(client, project_id, config):
    """Export project overview for 01_project_and_meta.md."""
    lines = []

    # --- Project info ---
    data = client.get(f"/projects/{project_id}.json", params={
        "include": "trackers,issue_categories,enabled_modules"
    })
    if not data or "project" not in data:
        return {"01_project_and_meta.md": "# Project: unknown\n"}

    p = data["project"]
    name = p.get("name", project_id)
    pid = p.get("identifier", "")
    created = fmt_date_only(p.get("created_on", ""))
    public = "yes" if p.get("is_public") else "no"

    lines.append(f"# Project: {name}")
    meta = f"ID:{pid} | Created:{created} | Public:{public}"
    parent = p.get("parent")
    if parent:
        meta += f" | Parent:{parent.get('name', '')}"
    lines.append(meta)
    lines.append("")

    desc = p.get("description", "")
    if desc:
        lines.append(desc)
        lines.append("")

    # --- Members ---
    print("  Members...")
    members = client.get_all(f"/projects/{project_id}/memberships.json", "memberships")
    if members:
        lines.append("## Members")
        lines.append("| Name | Roles |")
        lines.append("|------|-------|")
        for m in members:
            user = m.get("user") or m.get("group")
            uname = user.get("name", "?") if user else "?"
            roles = ", ".join(r.get("name", "") for r in m.get("roles", []))
            lines.append(f"| {uname} | {roles} |")
        lines.append("")

    # --- Trackers ---
    trackers = p.get("trackers", [])
    if trackers:
        lines.append("## Trackers")
        lines.append(", ".join(t.get("name", "") for t in trackers))
        lines.append("")

    # --- Statuses ---
    print("  Statuses...")
    data = client.get("/issue_statuses.json")
    if data and "issue_statuses" in data:
        lines.append("## Statuses")
        parts = []
        for s in data["issue_statuses"]:
            n = s.get("name", "")
            parts.append(f"{n}(closed)" if s.get("is_closed") else n)
        lines.append(", ".join(parts))
        lines.append("")

    # --- Priorities ---
    print("  Priorities...")
    data = client.get("/enumerations/issue_priorities.json")
    if data and "issue_priorities" in data:
        lines.append("## Priorities")
        parts = []
        for pr in data["issue_priorities"]:
            n = pr.get("name", "")
            parts.append(f"{n}(default)" if pr.get("is_default") else n)
        lines.append(", ".join(parts))
        lines.append("")

    # --- Categories ---
    cats = p.get("issue_categories", [])
    if cats:
        lines.append("## Categories")
        lines.append(", ".join(c.get("name", "") for c in cats))
        lines.append("")

    print(f"  -> Project overview done ({len(members)} members)")
    return {"01_project_and_meta.md": "\n".join(lines)}
