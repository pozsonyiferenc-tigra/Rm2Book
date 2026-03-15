"""DMSF (Document Management System) export - folder tree + file metadata + revisions."""

from redmine_export import fmt_date_only, short_name, fmt_size


def _walk_folder(client, project_id, folder_id=None, depth=0):
    """Recursively walk DMSF folder tree, returning formatted lines.

    Args:
        client: RedmineClient instance
        project_id: Redmine project identifier
        folder_id: DMSF folder ID (None for root)
        depth: Current nesting depth for indentation

    Returns:
        list of formatted output lines
    """
    indent = "  " * depth
    params = {}
    if folder_id:
        params["folder_id"] = folder_id

    data = client.get(f"/projects/{project_id}/dmsf.json", params=params)
    if not data:
        return []

    lines = []
    # Response structure: {"dmsf": {"dmsf_nodes": [...], "total_count": N, ...}}
    dmsf_data = data.get("dmsf", data)
    if isinstance(dmsf_data, dict):
        nodes = dmsf_data.get("dmsf_nodes", dmsf_data.get("nodes", []))
    elif isinstance(dmsf_data, list):
        nodes = dmsf_data
    else:
        nodes = []

    for node in nodes:
        ntype = node.get("type", "")
        title = node.get("title", node.get("name", ""))
        nid = node.get("id", "")

        if ntype == "folder" or ntype == "folder-link":
            lines.append(f"{indent}📁 {title}/")
            # Recurse into subfolder
            sub_lines = _walk_folder(client, project_id, nid, depth + 1)
            lines.extend(sub_lines)

        elif ntype in ("file", "file-link"):
            # Get detailed file metadata with revisions
            file_lines = _format_file(client, nid, depth)
            lines.extend(file_lines)

    return lines


def _format_file(client, file_id, depth=0):
    """Fetch file metadata and format with revision history.

    Args:
        client: RedmineClient instance
        file_id: DMSF file ID
        depth: Current nesting depth for indentation

    Returns:
        list of formatted output lines
    """
    indent = "  " * depth
    data = client.get(f"/dmsf/files/{file_id}.json")
    if not data:
        return [f"{indent}📎 [file:{file_id}] (metadata unavailable)"]

    # Handle different response structures
    file_info = data.get("dmsf_file", data.get("file", data))
    name = file_info.get("name", file_info.get("title", f"file:{file_id}"))
    revisions = file_info.get("revisions", file_info.get("dmsf_file_revisions", []))

    if not revisions:
        # Single line, no revision detail available
        return [f"{indent}📎 {name}"]

    if len(revisions) == 1:
        # Single revision — compact one-liner
        r = revisions[0]
        author = short_name(r.get("user", {}).get("name", "")) if isinstance(r.get("user"), dict) else ""
        date = fmt_date_only(r.get("updated_on", r.get("created_on", "")))
        size = fmt_size(r.get("size", 0))
        desc = r.get("description", r.get("comment", ""))
        version = r.get("version", r.get("name", ""))
        ver_str = f" v{version}" if version else ""
        desc_str = f' "{desc}"' if desc else ""
        return [f"{indent}📎 {name}{ver_str} ({author} {date} {size}){desc_str}"]

    # Multiple revisions — header + version list
    lines = [f"{indent}📎 {name} ({len(revisions)} revisions)"]
    for r in revisions:
        author = short_name(r.get("user", {}).get("name", "")) if isinstance(r.get("user"), dict) else ""
        date = fmt_date_only(r.get("updated_on", r.get("created_on", "")))
        size = fmt_size(r.get("size", 0))
        desc = r.get("description", r.get("comment", ""))
        version = r.get("version", r.get("name", ""))
        desc_str = f' "{desc}"' if desc else ""
        lines.append(f"{indent}  [v{version} {date} {author} {size}]{desc_str}")

    return lines


def export(client, project_id, config):
    """Export DMSF document tree with metadata and revisions."""
    print("  Fetching DMSF root folder...")

    # Test if DMSF is available
    data = client.get(f"/projects/{project_id}/dmsf.json")
    if not data:
        print("  DMSF not available or empty.")
        return {}

    # Check if there are any nodes at all
    dmsf_data = data.get("dmsf", data)
    if isinstance(dmsf_data, dict):
        nodes = dmsf_data.get("dmsf_nodes", [])
        total = dmsf_data.get("total_count", len(nodes))
    else:
        total = 0
    if total == 0:
        print("  DMSF is empty (0 documents).")
        return {}

    lines = ["## DMSF Documents\n"]
    folder_lines = _walk_folder(client, project_id)

    if not folder_lines:
        print("  No DMSF documents found.")
        return {}

    lines.extend(folder_lines)
    lines.append("")

    content = "\n".join(lines)
    file_count = sum(1 for l in folder_lines if "📎" in l and "revisions)" not in l and "[v" not in l)
    folder_count = sum(1 for l in folder_lines if "📁" in l)
    print(f"  -> DMSF done ({folder_count} folders, {file_count} files)")
    return {"01_project_and_meta.md": content}
