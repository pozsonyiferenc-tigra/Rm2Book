"""Issues export with full journal history, compact format."""

from redmine_export import fmt_date, fmt_date_only, short_name, fmt_size

# Relation type short codes
REL_PREFIX = {
    "relates": "~",
    "duplicates": "~dup:",
    "duplicated": "~duped:",
    "blocks": "~blocks:",
    "blocked": "~blocked:",
    "precedes": "~precedes:",
    "follows": "~follows:",
    "copied_to": "~copied:",
    "copied_from": "~from:",
}
DEFAULT_SPLIT_LIMIT = 450000

# Verbose: full English labels (self-documenting, no legend needed)
FIELD_CODES_VERBOSE = {
    "status_id": "Status",
    "priority_id": "Priority",
    "assigned_to_id": "Assigned",
    "fixed_version_id": "Version",
    "category_id": "Category",
    "tracker_id": "Tracker",
    "estimated_hours": "Estimated",
    "done_ratio": "Done",
    "subject": "Subject",
    "description": "Description",
    "start_date": "Start",
    "due_date": "Due",
    "parent_id": "Parent",
    "is_private": "Private",
}

# Compact: 1-letter codes (needs legend at file top)
FIELD_CODES_COMPACT = {
    "status_id": "S",
    "priority_id": "P",
    "assigned_to_id": "A",
    "fixed_version_id": "V",
    "category_id": "C",
    "tracker_id": "T",
    "estimated_hours": "Est",
    "done_ratio": "Done",
    "subject": "Subj",
    "description": "Desc",
    "start_date": "Start",
    "due_date": "Due",
    "parent_id": "Parent",
    "is_private": "Private",
}

# Meta line field prefixes per mode
META_FIELDS_VERBOSE = {
    "priority": "Priority:", "assigned": "Assigned:", "version": "Version:",
    "category": "Category:", "estimated": "Estimated:", "spent": "Spent:",
    "done": "Done:",
}
META_FIELDS_COMPACT = {
    "priority": "P:", "assigned": "A:", "version": "V:",
    "category": "C:", "estimated": "Est:", "spent": "Spent:",
    "done": "Done:",
}

LEGEND = "S=Status P=Priority A=Assigned V=Version C=Category T=Tracker"


def _build_lookups(client):
    """Pre-fetch enumerations for ID->name resolution in journals."""
    lookups = {}

    data = client.get("/issue_statuses.json")
    if data:
        lookups["status_id"] = {str(s["id"]): s["name"] for s in data.get("issue_statuses", [])}

    data = client.get("/enumerations/issue_priorities.json")
    if data:
        lookups["priority_id"] = {str(p["id"]): p["name"] for p in data.get("issue_priorities", [])}

    data = client.get("/trackers.json")
    if data:
        lookups["tracker_id"] = {str(t["id"]): t["name"] for t in data.get("trackers", [])}

    return lookups


def _resolve(lookups, field_name, value):
    """Resolve an ID to a name using lookups, or return value as-is."""
    if not value:
        return ""
    table = lookups.get(field_name)
    if table:
        return table.get(str(value), str(value))
    return str(value)


def _format_issue(issue, lookups, compact=False):
    """Format a single issue. compact=True uses 1-letter codes."""
    field_codes = FIELD_CODES_COMPACT if compact else FIELD_CODES_VERBOSE
    mf = META_FIELDS_COMPACT if compact else META_FIELDS_VERBOSE

    lines = []
    tracker = issue.get("tracker", {}).get("name", "")
    iid = issue.get("id", "")
    subject = issue.get("subject", "")
    status = issue.get("status", {}).get("name", "")

    # Header
    lines.append(f"## ID:{iid} [{tracker}] {subject} ({status})")

    # Meta line: only non-empty fields
    meta = []
    priority = issue.get("priority", {}).get("name", "")
    if priority:
        meta.append(f"{mf['priority']}{priority}")
    assigned = issue.get("assigned_to", {})
    if assigned:
        meta.append(f"{mf['assigned']}{assigned.get('name', '')}")
    version = issue.get("fixed_version", {})
    if version:
        meta.append(f"{mf['version']}{version.get('name', '')}")
    category = issue.get("category", {})
    if category:
        meta.append(f"{mf['category']}{category.get('name', '')}")
    parent = issue.get("parent", {})
    if parent:
        meta.append(f"^ID:{parent.get('id', '')}")

    # Date range
    created = fmt_date_only(issue.get("created_on", ""))
    closed = fmt_date_only(issue.get("closed_on", ""))
    updated = fmt_date_only(issue.get("updated_on", ""))
    if created:
        end = closed or updated or ""
        meta.append(f"{created}..{end}" if end and end != created else created)

    if issue.get("estimated_hours"):
        meta.append(f"{mf['estimated']}{issue['estimated_hours']}h")
    if issue.get("spent_hours"):
        meta.append(f"{mf['spent']}{issue['spent_hours']}h")
    if issue.get("done_ratio"):
        meta.append(f"{mf['done']}{issue['done_ratio']}%")

    # Custom fields in meta
    for cf in issue.get("custom_fields", []):
        val = cf.get("value", "")
        if isinstance(val, list):
            val = ",".join(str(v) for v in val)
        if val:
            meta.append(f"cf:{cf.get('name', '')}:{val}")

    if meta:
        lines.append(" | ".join(meta))
    lines.append("")

    # Description
    desc = issue.get("description", "")
    if desc:
        lines.append(desc)
        lines.append("")

    # Journals
    for j in issue.get("journals", []):
        user = short_name(j.get("user", {}).get("name", "?"))
        date = fmt_date(j.get("created_on", ""))
        notes = (j.get("notes") or "").strip()
        details = j.get("details", [])

        # Format field changes
        changes = []
        for d in details:
            prop = d.get("property", "")
            name = d.get("name", "")
            old = d.get("old_value", "") or ""
            new = d.get("new_value", "") or ""

            if prop == "attr":
                code = field_codes.get(name, name)
                old_resolved = _resolve(lookups, name, old)
                new_resolved = _resolve(lookups, name, new)
                if old_resolved:
                    changes.append(f"{code}:{old_resolved}→{new_resolved}")
                else:
                    changes.append(f"{code}:→{new_resolved}")
            elif prop == "cf":
                if old:
                    changes.append(f"cf{name}:{old}→{new}")
                else:
                    changes.append(f"cf{name}:→{new}")
            elif prop == "attachment":
                changes.append(f"+📎{new}")
            elif prop == "relation":
                changes.append(f"rel:{name}→{new}")

        change_str = " | ".join(changes)

        if notes and changes:
            lines.append(f"[{date} {user}] \"{notes}\"")
            lines.append(f"  {change_str}")
        elif notes:
            lines.append(f"[{date} {user}] \"{notes}\"")
        elif changes:
            lines.append(f"[{date} {user}] {change_str}")

    # Attachments
    for a in issue.get("attachments", []):
        author = short_name(a.get("author", {}).get("name", ""))
        date = fmt_date_only(a.get("created_on", ""))
        size = fmt_size(a.get("filesize", 0))
        desc = f" \"{a['description']}\"" if a.get("description") else ""
        lines.append(f"📎 {a.get('filename', '')} ({author} {date} {size}){desc}")

    # Relations
    for r in issue.get("relations", []):
        rtype = r.get("relation_type", "relates")
        other = r.get("issue_to_id", "")
        if other == iid:
            other = r.get("issue_id", "")
        prefix = REL_PREFIX.get(rtype, "~")
        lines.append(f"{prefix}ID:{other}")

    # Children
    for c in issue.get("children", []):
        lines.append(f"^ID:{c.get('id', '')} {c.get('subject', '')}")

    lines.append("\n---\n")
    return "\n".join(lines)


def export(client, project_id, config):
    """Export all issues with full history."""
    compact = config.get("compact_fields", False)

    print("  Building lookups...")
    lookups = _build_lookups(client)

    print("  Fetching issues (all statuses)...")

    def on_progress(fetched, total):
        print(f"\r  {fetched}/{total} issues...", end="", flush=True)

    all_issues = client.get_all(
        "/issues.json",
        "issues",
        params={
            "project_id": project_id,
            "status_id": "*",
            "sort": "id:asc",
            "include": "journals,attachments,relations,children",
        },
        on_progress=on_progress,
    )
    print(f"\r  -> {len(all_issues)} issues fetched.          ")

    if not all_issues:
        return {"02_issues.md": f"# Issues [{project_id}] (0)\n"}

    # Build header
    header = f"# Issues [{project_id}] ({len(all_issues)})\n"
    if compact:
        header += f"{LEGEND}\n"
    header += "\n---\n\n"

    # Format all issues, split by word count if needed
    max_words = config.get("split_limit_words", DEFAULT_SPLIT_LIMIT)
    files = {}
    current_content = header
    file_num = 1

    for issue in all_issues:
        formatted = _format_issue(issue, lookups, compact=compact)

        # Check if adding this issue would exceed limit
        combined = current_content + formatted + "\n"
        if len(combined.split()) > max_words and current_content != header:
            # Save current file and start new one
            fname = f"02_issues_{file_num:03d}.md" if file_num > 1 or True else "02_issues.md"
            files[fname] = current_content
            file_num += 1
            current_content = header + formatted + "\n"
        else:
            current_content = combined

    # Save last file
    if file_num == 1:
        files["02_issues.md"] = current_content
    else:
        files[f"02_issues_{file_num:03d}.md"] = current_content
        # Rename first file if we split
        if "02_issues.md" not in files and "02_issues_001.md" not in files:
            pass  # Already named correctly

    if file_num > 1:
        print(f"  -> Split into {file_num} files")
    return files
