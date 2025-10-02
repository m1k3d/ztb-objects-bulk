#!/usr/bin/env python3
"""
objects_bulk.py — create ZTB Objects in bulk from CSV, with row-grouping.

CSV format (headers required):
  name,type,items
Rows with the same (name,type) are grouped; their `items` are aggregated.

Examples:
  name,type,items
  Whitelist-ZCC,domains,domain1.com
  Whitelist-ZCC,domains,domain2.com
  Mike-DC,network,172.16.50.0/24
  Mike-DC,network,172.16.51.0/24

.env expected:
  BASE_URL="https://<vanity>-api.goairgap.com"
  BEARER="Bearer eyJ..."
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from jinja2 import Environment, FileSystemLoader, StrictUndefined

# Optional: load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass


def getenv_clean(key: str, default: str = "") -> str:
    val = os.getenv(key, default)
    return val.strip() if val else ""


def normalize_bearer(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    return raw if raw.lower().startswith("bearer ") else f"Bearer {raw}"


def read_and_group(csv_path: Path) -> Dict[Tuple[str, str], Dict[str, object]]:
    """
    Returns a dict: (name,type) -> {"name": name, "type": type, "items": [..]}
    Groups rows; de-duplicates items per group.
    """
    groups: Dict[Tuple[str, str], Dict[str, object]] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # start=2 because header is line 1
            try:
                name = row["name"].strip()
                typ = row["type"].strip().lower()
                item = row["items"].strip()
            except KeyError as e:
                raise SystemExit(f"❌ CSV missing required column: {e}. Required: name,type,items")

            if not name or not typ or not item:
                print(f"⚠️  Skip line {i}: blank field(s): {row}")
                continue

            if typ not in {"domains", "network"}:
                print(f"⚠️  Skip line {i}: unsupported type '{typ}' (use 'domains' or 'network')")
                continue

            key = (name, typ)
            if key not in groups:
                groups[key] = {"name": name, "type": typ, "items": []}

            # de-dup within group
            if item not in groups[key]["items"]:
                groups[key]["items"].append(item)

    return groups


def main():
    ap = argparse.ArgumentParser(description="Bulk create ZTB Objects from CSV (grouped by name+type)")
    ap.add_argument("--csv", default="objects.csv", help="Path to CSV (default: objects.csv)")
    ap.add_argument("--template", default="templates/object_payload.json.j2",
                    help="Jinja2 template path (default: templates/object_payload.json.j2)")
    ap.add_argument("--dry-run", action="store_true", help="Print payloads but do not POST")
    ap.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = ap.parse_args()

    base_url = getenv_clean("BASE_URL")
    bearer = normalize_bearer(getenv_clean("BEARER"))

    if not base_url or not bearer:
        print("❌ BASE_URL and/or BEARER missing. Put them in .env or export in shell.")
        print('   Example .env:\n     BASE_URL="https://<vanity>-api.goairgap.com"\n     BEARER="Bearer eyJ..."')
        sys.exit(1)

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        sys.exit(1)

    template_path = Path(args.template).resolve()
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        sys.exit(1)

    # Group & prepare
    groups = read_and_group(csv_path)
    if not groups:
        print("ℹ️  Nothing to do (no valid rows).")
        return

    # Jinja env
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(template_path.name)

    # API endpoint
    url = f"{base_url.rstrip('/')}/api/v2/groups?refresh_token=enabled"
    headers = {
        "Authorization": bearer,
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
    }

    created = 0
    skipped = 0
    errors = 0

    for (name, typ), data in groups.items():
        payload_str = tpl.render(name=name, type=typ, items=data["items"])
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError as e:
            print(f"❌ Bad JSON for group '{name}' ({typ}): {e}")
            errors += 1
            continue

        if args.verbose or args.dry_run:
            print("\n--- payload --------------------------------")
            print(json.dumps(payload, indent=2))
            print("-------------------------------------------")

        if args.dry_run:
            skipped += 1
            continue

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                created += 1
                if args.verbose:
                    print(f"✅ Created '{name}' ({typ})")
            elif resp.status_code == 409:
                # If you want to update instead, this is the spot to add upsert logic.
                print(f"⚠️  Exists (409): '{name}' ({typ}) — skipping")
                skipped += 1
            else:
                snippet = resp.text[:300].replace("\n", " ")
                print(f"❌ Error {resp.status_code} creating '{name}' ({typ}): {snippet}")
                errors += 1
        except requests.RequestException as e:
            print(f"❌ Request failed for '{name}' ({typ}): {e}")
            errors += 1

    print("\n== Summary ==")
    print(f"Created: {created}")
    if args.dry_run:
        print(f"Previewed (dry-run): {skipped}")
    else:
        print(f"Skipped: {skipped}")
    print(f"Errors:  {errors}")


if __name__ == "__main__":
    main()