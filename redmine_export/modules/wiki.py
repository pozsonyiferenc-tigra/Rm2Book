"""Wiki pages export with full version history."""

import hashlib

from redmine_export import fmt_date_only, short_name, fmt_size, word_count

DEFAULT_SPLIT_LIMIT = 450000


def _format_page(client, project_id, page_info, config):
    """Format a single wiki page. Returns (title, content_string, skipped_count)."""
    wiki_mode = config.get("wiki_versions", "all")
    title = page_info.get("title", "")
    print(f"    {title}...", end="", flush=True)

    page_data = client.get(
        f"/projects/{project_id}/wiki/{title}.json",
        params={"include": "attachments"},
    )
    if not page_data or "wiki_page" not in page_data:
        print(" skip")
        return title, None, 0

    current = page_data["wiki_page"]
    current_version = current.get("version", 1)

    lines = [f"## {title}"]
    page_skipped = 0

    if wiki_mode == "latest":
        author = short_name(current.get("author", {}).get("name", ""))
        date = fmt_date_only(current.get("updated_on", current.get("created_on", "")))
        text = current.get("text", "")
        lines.append(f"[v{current_version} {date} {author}] {text}")
        lines.append("")
        print(f" v{current_version}")
    else:
        prev_hash = None

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

            text_hash = hashlib.md5(text.encode()).hexdigest()

            if text_hash == prev_hash:
                page_skipped += 1
                continue

            lines.append(f"[v{v} {date} {author}] {text}")
            lines.append("")
            prev_hash = text_hash

        skip_info = f" -{page_skipped}dup" if page_skipped else ""
        print(f" v{current_version}{skip_info}")

    # Attachments
    for a in current.get("attachments", []):
        author = short_name(a.get("author", {}).get("name", ""))
        date = fmt_date_only(a.get("created_on", ""))
        size = fmt_size(a.get("filesize", 0))
        lines.append(f"📎 {a.get('filename', '')} ({author} {date} {size})")

    lines.append("")
    return title, "\n".join(lines), page_skipped


def export(client, project_id, config):
    """Export all wiki pages with version history and word-count splitting."""
    print("  Fetching wiki index...")
    data = client.get(f"/projects/{project_id}/wiki/index.json")
    if not data or "wiki_pages" not in data:
        return {"03_wiki.md": f"# Wiki [{project_id}] (0 pages)\n"}

    pages = data["wiki_pages"]
    wiki_mode = config.get("wiki_versions", "all")
    print(f"  {len(pages)} wiki pages found (versions: {wiki_mode})")

    # Phase 1: format all pages
    formatted_pages = []  # list of (title, content)
    total_skipped = 0

    for page_info in sorted(pages, key=lambda p: p.get("title", "")):
        title, content, skipped = _format_page(client, project_id, page_info, config)
        if content is not None:
            formatted_pages.append((title, content))
            total_skipped += skipped

    if not formatted_pages:
        return {"03_wiki.md": f"# Wiki [{project_id}] (0 pages)\n"}

    # Phase 2: split into chunks by word count (page boundaries)
    max_words = config.get("split_limit_words", DEFAULT_SPLIT_LIMIT)
    header = f"# Wiki [{project_id}] ({len(formatted_pages)} pages)\n\n"

    chunks = []  # list of (content, title_list)
    current_content = ""
    current_titles = []

    for title, content in formatted_pages:
        combined = current_content + content + "\n"
        if word_count(combined) > max_words and current_content:
            chunks.append((current_content, current_titles))
            current_content = content + "\n"
            current_titles = [title]
        else:
            current_content = combined
            current_titles.append(title)

    if current_content:
        chunks.append((current_content, current_titles))

    # Phase 3: build files with TOC
    files = {}
    for i, (content, title_list) in enumerate(chunks):
        toc_lines = ["## Contents\n"]
        for t in title_list:
            toc_lines.append(f"- {t}")
        toc_lines.append("\n---\n")
        toc = "\n".join(toc_lines)

        full = header + toc + content

        if len(chunks) == 1:
            files["03_wiki.md"] = full
        else:
            files[f"03_wiki_{i+1:03d}.md"] = full

    skip_msg = f", {total_skipped} duplicate versions skipped" if total_skipped else ""
    split_msg = f", split into {len(chunks)} files" if len(chunks) > 1 else ""
    print(f"  -> Wiki done ({len(formatted_pages)} pages{skip_msg}{split_msg})")
    return files
