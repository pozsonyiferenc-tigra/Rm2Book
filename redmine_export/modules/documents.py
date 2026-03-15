"""Redmine built-in Documents module export (metadata + descriptions)."""

from redmine_export import fmt_date_only, short_name, fmt_size


def export(client, project_id, config):
    """Export documents metadata and descriptions for 01_project_and_meta.md."""
    print("  Fetching documents...")
    data = client.get(f"/projects/{project_id}/documents.json")
    if not data or "documents" not in data:
        return {}

    doc_list = data["documents"]
    if not doc_list:
        return {}

    lines = ["\n## Documents\n"]

    for doc in sorted(doc_list, key=lambda d: d.get("created_on", "")):
        title = doc.get("title", "")
        desc = doc.get("description", "")
        date = fmt_date_only(doc.get("created_on", ""))
        category = doc.get("category", {}).get("name", "") if isinstance(doc.get("category"), dict) else ""

        # Header line
        header = f"### {title}"
        if category:
            header += f" [{category}]"
        header += f" ({date})"
        lines.append(header)

        if desc:
            lines.append(desc)

        # Fetch document detail with attachments
        doc_id = doc.get("id")
        if doc_id:
            detail = client.get(f"/documents/{doc_id}.json", params={"include": "attachments"})
            if detail and "document" in detail:
                attachments = detail["document"].get("attachments", [])
                for a in attachments:
                    author = short_name(a.get("author", {}).get("name", ""))
                    adate = fmt_date_only(a.get("created_on", ""))
                    size = fmt_size(a.get("filesize", 0))
                    fname = a.get("filename", "")
                    adesc = a.get("description", "")
                    entry = f"📎 {fname} ({author} {adate} {size})"
                    if adesc:
                        entry += f' "{adesc}"'
                    lines.append(entry)

        lines.append("")

    print(f"  -> {len(doc_list)} documents")
    return {"01_project_and_meta.md": "\n".join(lines)}
