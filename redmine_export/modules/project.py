"""Project overview: info, members, trackers, statuses, priorities, categories, project tree."""

from redmine_export import fmt_date_only


def _build_project_tree(all_projects, project_numeric_id, indent=0):
    """Build indented tree of descendant projects."""
    children = [
        p for p in all_projects
        if p.get("parent", {}).get("id") == project_numeric_id
    ]
    lines = []
    for child in sorted(children, key=lambda p: p.get("name", "")):
        cid = child.get("identifier", "")
        cname = child.get("name", cid)
        prefix = "  " * indent + "- "
        lines.append(f"{prefix}{cid} ({cname})")
        lines.extend(_build_project_tree(all_projects, child.get("id"), indent + 1))
    return lines


def export(client, project_id, config):
    """Export project overview for 01_project_and_meta.md."""
    lines = []

    # --- Project info ---
    data = client.get(f"/projects/{project_id}.json", params={
        "include": "trackers,issue_categories,enabled_modules"
    })
    if not data or "project" not in data:
        return {"01_project_and_meta.md": f"# Project: {project_id}\n"}

    p = data["project"]
    name = p.get("name", project_id)
    pid = p.get("identifier", "")
    numeric_id = p.get("id")
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

    # --- Project Tree: parent + descendants ---
    print("  Project tree...")
    all_projects = client.get_all("/projects.json", "projects", params={"limit": 100})

    tree_lines = []

    # Show parent chain
    if parent:
        parent_id = parent.get("id")
        parent_proj = next((pp for pp in all_projects if pp.get("id") == parent_id), None)
        if parent_proj:
            tree_lines.append(f"Parent: {parent_proj.get('identifier', '')} ({parent_proj.get('name', '')})")

    # Show descendants
    descendants = _build_project_tree(all_projects, numeric_id)
    if descendants:
        tree_lines.append("Children:")
        tree_lines.extend(descendants)

    if tree_lines:
        lines.append("## Project Tree")
        lines.extend(tree_lines)
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
