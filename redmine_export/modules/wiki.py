"""Wiki pages export with full version history, including subprojects."""

from redmine_export import fmt_date_only, short_name, fmt_size


def _get_subprojects_recursive(client, project_id):
    """Recursively collect all subproject identifiers under a project.

    Uses /projects.json listing and filters by parent ID, since
    /projects/{id}.json?include=children may not return children in all
    Redmine versions.

    Returns list of (project_id, project_name) tuples, depth-first order.
    """
    # First, get the numeric ID of the parent project
    data = client.get(f"/projects/{project_id}.json")
    if not data or "project" not in data:
        return []
    parent_numeric_id = data["project"].get("id")
    if not parent_numeric_id:
        return []

    # Fetch all visible projects and filter by parent
    all_projects = client.get_all("/projects.json", "projects", params={"limit": 100})
    children = [
        p for p in all_projects
        if p.get("parent", {}).get("id") == parent_numeric_id
    ]

    result = []
    for child in children:
        cid = child.get("identifier", "")
        cname = child.get("name", cid)
        if cid:
            result.append((cid, cname))
            # Recurse: find grandchildren by this child's numeric ID
            child_numeric_id = child.get("id")
            grandchildren = [
                p for p in all_projects
                if p.get("parent", {}).get("id") == child_numeric_id
            ]
            for gc in grandchildren:
                gcid = gc.get("identifier", "")
                gcname = gc.get("name", gcid)
                if gcid:
                    result.append((gcid, gcname))
                    # Continue recursion for deeper levels
                    result.extend(_get_deep_children(all_projects, gc.get("id")))
    return result


def _get_deep_children(all_projects, parent_id):
    """Find children at deeper levels from the already-fetched project list."""
    if not parent_id:
        return []
    children = [
        p for p in all_projects
        if p.get("parent", {}).get("id") == parent_id
    ]
    result = []
    for child in children:
        cid = child.get("identifier", "")
        cname = child.get("name", cid)
        if cid:
            result.append((cid, cname))
            result.extend(_get_deep_children(all_projects, child.get("id")))
    return result


def _export_wiki_for_project(client, project_id):
    """Export all wiki pages for a single project.

    Returns (list_of_lines, page_count).
    """
    data = client.get(f"/projects/{project_id}/wiki/index.json")
    if not data or "wiki_pages" not in data:
        return [], 0

    pages = data["wiki_pages"]
    lines = []

    for page_info in sorted(pages, key=lambda p: p.get("title", "")):
        title = page_info.get("title", "")
        print(f"    {title}...", end="", flush=True)

        page_data = client.get(
            f"/projects/{project_id}/wiki/{title}.json",
            params={"include": "attachments"},
        )
        if not page_data or "wiki_page" not in page_data:
            print(" skip")
            continue

        current = page_data["wiki_page"]
        current_version = current.get("version", 1)
        print(f" v{current_version}")

        # Header with project identifier
        lines.append(f"## {title} [{project_id}]")

        # Fetch all versions from newest to oldest
        for v in range(current_version, 0, -1):
            if v == current_version:
                author = short_name(current.get("author", {}).get("name", ""))
                date = fmt_date_only(current.get("updated_on", current.get("created_on", "")))
                text = current.get("text", "")
            else:
                vdata = client.get(f"/projects/{project_id}/wiki/{title}/{v}.json")
                if not vdata or "wiki_page" not in vdata:
                    continue
                vpage = vdata["wiki_page"]
                author = short_name(vpage.get("author", {}).get("name", ""))
                date = fmt_date_only(vpage.get("updated_on", vpage.get("created_on", "")))
                text = vpage.get("text", "")

            lines.append(f"[v{v} {date} {author}] {text}")
            lines.append("")

        # Attachments
        for a in current.get("attachments", []):
            author = short_name(a.get("author", {}).get("name", ""))
            date = fmt_date_only(a.get("created_on", ""))
            size = fmt_size(a.get("filesize", 0))
            lines.append(f"📎 {a.get('filename', '')} ({author} {date} {size})")

        lines.append("")

    return lines, len(pages)


def export(client, project_id, config):
    """Export all wiki pages with all versions, including subprojects (recursive)."""
    # Collect all projects: main + subprojects
    projects = [(project_id, project_id)]  # (id, name)

    print("  Fetching subprojects (recursive)...")
    subprojects = _get_subprojects_recursive(client, project_id)
    if subprojects:
        print(f"  Found {len(subprojects)} subprojects: {', '.join(s[0] for s in subprojects)}")
        projects.extend(subprojects)

    total_pages = 0
    all_lines = []

    for pid, pname in projects:
        print(f"  Fetching wiki for [{pid}]...")
        lines, page_count = _export_wiki_for_project(client, pid)
        total_pages += page_count
        all_lines.extend(lines)

    # Build header
    project_count = len(projects)
    if project_count > 1:
        header = f"# Wiki ({total_pages} pages, {project_count} projects)\n"
    else:
        header = f"# Wiki ({total_pages} pages)\n"

    content = header + "\n".join(all_lines)
    print(f"  -> Wiki done ({total_pages} pages across {project_count} projects)")
    return {"03_wiki.md": content}
