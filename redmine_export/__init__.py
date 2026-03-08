"""Shared utilities for compact output format."""


def fmt_date(iso_str):
    """ISO date to compact YYMMDD HH:MM. '2024-01-15T10:30:22Z' -> '240115 10:30'"""
    if not iso_str:
        return ""
    d = iso_str.replace("T", " ").replace("Z", "")
    if len(d) >= 16:
        return d[2:4] + d[5:7] + d[8:10] + " " + d[11:16]
    if len(d) >= 10:
        return d[2:4] + d[5:7] + d[8:10]
    return iso_str


def fmt_date_only(iso_str):
    """ISO date to compact YYMMDD (no time). '2024-01-15' -> '240115'"""
    if not iso_str:
        return ""
    d = iso_str.replace("T", " ").replace("Z", "")
    if len(d) >= 10:
        return d[2:4] + d[5:7] + d[8:10]
    return iso_str


def short_name(full_name):
    """'Kiss János' -> 'Kiss J.' / 'Kiss János Péter' -> 'Kiss J. P.'"""
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name
    return parts[0] + " " + " ".join(p[0] + "." for p in parts[1:])


def fmt_size(bytes_val):
    """Compact file size: 1234 -> '1KB', 1234567 -> '1.2MB'"""
    if not bytes_val:
        return "0B"
    if bytes_val < 1024:
        return f"{bytes_val}B"
    if bytes_val < 1024 * 1024:
        return f"{bytes_val // 1024}KB"
    return f"{bytes_val / (1024 * 1024):.1f}MB"


def word_count(text):
    """Approximate word count for NotebookLM limit checking."""
    return len(text.split())
