"""Wiki pages export with full version history."""

from redmine_export import fmt_date_only, short_name


def export(client, project_id, config):
    """Export all wiki pages with all versions, newest first."""
    print("  Fetching wiki index...")
    data = client.get(f"/projects/{project_id}/wiki/index.json")
    if not data or "wiki_pages" not in data:
        return {"03_wiki.md": "# Wiki (0)\n"}

    pages = data["wiki_pages"]
    print(f"  {len(pages)} wiki pages found")
    lines = [f"# Wiki ({len(pages)} pages)\n"]

    for page_info in sorted(pages, key=lambda p: p.get("title", "")):
        title = page_info.get("title", "")
        print(f"    {title}...", end="", flush=True)

        # Get current version (has version number)
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

        lines.append(f"## {title}")

        # Fetch all versions from newest to oldest
        for v in range(current_version, 0, -1):
            if v == current_version:
                # Use already fetched current version
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
            from redmine_export import fmt_size
            author = short_name(a.get("author", {}).get("name", ""))
            date = fmt_date_only(a.get("created_on", ""))
            size = fmt_size(a.get("filesize", 0))
            lines.append(f"📎 {a.get('filename', '')} ({author} {date} {size})")

        lines.append("")

    print(f"  -> Wiki done ({len(pages)} pages)")
    return {"03_wiki.md": "\n".join(lines)}
