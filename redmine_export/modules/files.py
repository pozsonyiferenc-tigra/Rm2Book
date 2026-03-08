"""Project files metadata export."""

from redmine_export import fmt_date_only, short_name, fmt_size


def export(client, project_id, config):
    """Export file metadata for 01_project_and_meta.md."""
    print("  Fetching files...")
    data = client.get(f"/projects/{project_id}/files.json")
    if not data or "files" not in data:
        return {}

    file_list = data["files"]
    if not file_list:
        return {}

    lines = ["\n## Files\n"]
    for f in file_list:
        author = short_name(f.get("author", {}).get("name", ""))
        date = fmt_date_only(f.get("created_on", ""))
        size = fmt_size(f.get("filesize", 0))
        desc = f.get("description", "")
        fname = f.get("filename", "")

        entry = f"📎 {fname} ({author} {date} {size})"
        if desc:
            entry += f" \"{desc}\""
        lines.append(entry)

    lines.append("")
    print(f"  -> {len(file_list)} files")
    return {"01_project_and_meta.md": "\n".join(lines)}
