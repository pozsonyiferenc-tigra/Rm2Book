#!/usr/bin/env python3
"""Rm2Book - Redmine to NotebookLM export tool.

Usage:
    python run.py                          # Uses config.json
    python run.py --config my_config.json  # Custom config
    python run.py --output-dir export/     # Override output dir
"""

import argparse
import json
import sys
import os

from redmine_export.client import RedmineClient
from redmine_export.exporter import run_export


def main():
    parser = argparse.ArgumentParser(
        description="Export Redmine project data to AI-friendly markdown"
    )
    parser.add_argument(
        "--config", default="config.json",
        help="Config file path (default: config.json)"
    )
    parser.add_argument(
        "--output-dir",
        help="Override output directory from config"
    )
    parser.add_argument(
        "--modules", nargs="*",
        help="Only run specific modules (e.g. --modules issues wiki)"
    )
    args = parser.parse_args()

    # Load config
    if not os.path.exists(args.config):
        print(f"Config file not found: {args.config}")
        print(f"Copy config.example.json to config.json and fill in your details.")
        sys.exit(1)

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validate required fields
    for field in ("redmine_url", "api_key", "project_id"):
        if not config.get(field) or config[field].startswith("YOUR_"):
            print(f"Missing or placeholder value for '{field}' in {args.config}")
            sys.exit(1)

    # Apply CLI overrides
    if args.output_dir:
        config["output_dir"] = args.output_dir
    if args.modules:
        config["modules"] = args.modules

    # Run export
    print(f"Rm2Book - Exporting project: {config['project_id']}")
    print(f"Redmine: {config['redmine_url']}")
    print(f"Output: {config.get('output_dir', 'output')}/")

    client = RedmineClient(config["redmine_url"], config["api_key"])
    run_export(client, config["project_id"], config)


if __name__ == "__main__":
    main()
