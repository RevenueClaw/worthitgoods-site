#!/usr/bin/env python3
"""
WorthItGoods Memory Consolidation
==================================
Reads today's memory file, checks for stale WorthItGoods entries, and
generates a summary report. No fragile MEMORY.md edits — just reports
what needs attention for manual review.

Usage: python3 scripts/consolidate_memory.py
"""

import os
import json
import re
from datetime import datetime, timezone, timedelta

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
MEMORY_FILE = os.path.join(WORKSPACE, "MEMORY.md")
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
YESTERDAY = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
MEMORY_DIR = os.path.join(WORKSPACE, "memory")


def check_memory_section():
    """Check the WorthItGoods section in MEMORY.md for stale entries."""
    if not os.path.exists(MEMORY_FILE):
        return [], "MEMORY.md not found"
    
    issues = []
    with open(MEMORY_FILE) as f:
        content = f.read()
    
    # Find WorthItGoods section
    match = re.search(r'^### WorthItGoods\.com\s*\n(.*?)(?=^### |\Z)', content, re.MULTILINE | re.DOTALL)
    if not match:
        # Try without .com
        match = re.search(r'^### WorthItGoods\s*\n(.*?)(?=^### |\Z)', content, re.MULTILINE | re.DOTALL)
    
    if not match:
        return ["WorthItGoods section not found in MEMORY.md"], "Section missing"
    
    section = match.group(1)
    
    # Check for premortem entries older than 1 week
    for line in section.split('\n'):
        if 'premortem' in line.lower() or 'premortem-fixed' in line.lower():
            # Check if it has a date
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if date_match:
                entry_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if (datetime.now(timezone.utc) - entry_date).days > 7:
                    issues.append(f"Stale premortem entry: {line.strip()[:80]}")
    
    return issues, "OK"


def check_today_memory():
    """Check if today's memory file exists and has content."""
    today_file = os.path.join(MEMORY_DIR, f"{TODAY}.md")
    yesterday_file = os.path.join(MEMORY_DIR, f"{YESTERDAY}.md")
    
    for f, label in [(today_file, "Today"), (yesterday_file, "Yesterday")]:
        if os.path.exists(f):
            with open(f) as fh:
                content = fh.read()
            wig_lines = [l for l in content.split('\n') if 'worthitgoods' in l.lower() or 'WorthItGoods' in l]
            print(f"  {label} ({os.path.basename(f)}): {len(wig_lines)} WorthItGoods-related lines")
        else:
            print(f"  {label}: No file")


def main():
    print(f"WorthItGoods Memory Consolidation — {TODAY}")
    print(f"{'='*50}")
    
    # Check daily memory files
    check_today_memory()
    
    # Check MEMORY.md section
    issues, status = check_memory_section()
    print(f"\n  MEMORY.md section: {status}")
    if issues:
        print(f"  Issues found ({len(issues)}):")
        for issue in issues:
            print(f"    ⚠️ {issue}")
    else:
        print(f"  No stale entries found")
    
    # Check HEARTBEAT.md for WorthItGoods entries
    heartbeat_file = os.path.join(WORKSPACE, "HEARTBEAT.md")
    if os.path.exists(heartbeat_file):
        with open(heartbeat_file) as f:
            hb = f.read()
        wig_hb = [l for l in hb.split('\n') if 'worthitgoods' in l.lower() or 'WorthItGoods' in l]
        print(f"\n  HEARTBEAT.md: {len(wig_hb)} WorthItGoods-related lines")
    
    print(f"\n{'='*50}")
    print(f"Consolidation complete. No changes made to MEMORY.md.")
    print(f"To update MEMORY.md manually: edit ~/.openclaw/workspace/MEMORY.md")


if __name__ == "__main__":
    main()