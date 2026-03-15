"""Main export orchestrator. Runs modules and writes output files."""

import os
import importlib
import time

from redmine_export import word_count

# Module execution order -> target output files
MODULE_ORDER = [
    "project",       # -> 01_project_and_meta.md
    "versions",      # -> 01_project_and_meta.md
    "files",         # -> 01_project_and_meta.md
    "dmsf",          # -> 01_project_and_meta.md
    "issues",        # -> 02_issues.md (may split)
    "wiki",          # -> 03_wiki.md (includes subproject wikis)
    "news",          # -> 04_activity.md
    "time_entries",  # -> 04_activity.md
]

MAX_WORDS = 450000  # Safety margin under NotebookLM's 500K limit


def run_export(client, project_id, config):
    """Run all enabled modules and write output files.

    Returns:
        dict with export statistics.
    """
    output_dir = config.get("output_dir", "output")
    enabled = config.get("modules", MODULE_ORDER)
    os.makedirs(output_dir, exist_ok=True)

    # Collect outputs from all modules
    all_files = {}
    stats = {}
    start = time.time()

    for module_name in MODULE_ORDER:
        if module_name not in enabled:
            continue

        print(f"\n[{module_name}]")
        try:
            mod = importlib.import_module(f"redmine_export.modules.{module_name}")
            result = mod.export(client, project_id, config)

            for filename, content in result.items():
                if filename in all_files:
                    all_files[filename] += "\n" + content
                else:
                    all_files[filename] = content

            stats[module_name] = "ok"
        except Exception as e:
            print(f"  [!] Error: {e}")
            stats[module_name] = f"error: {e}"

    # Write files with word count check
    print(f"\n--- Writing output ---")
    total_words = 0
    for filename, content in sorted(all_files.items()):
        filepath = os.path.join(output_dir, filename)
        wc = word_count(content)
        total_words += wc

        if wc > MAX_WORDS:
            print(f"  [!] {filename}: {wc} words exceeds {MAX_WORDS} limit!")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {filename} ({wc:,} words, {len(content):,} chars)")

    elapsed = time.time() - start
    print(f"\n--- Done ---")
    print(f"  Files: {len(all_files)}")
    print(f"  Total words: {total_words:,}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Output: {os.path.abspath(output_dir)}/")

    stats["_total_files"] = len(all_files)
    stats["_total_words"] = total_words
    stats["_elapsed"] = elapsed
    return stats
