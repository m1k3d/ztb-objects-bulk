#!/usr/bin/env python3
"""
objects_bulk.py — Create ZTB Objects in bulk from CSV (grouped by name+type) with auto-login & 401 refresh.

CSV format (headers required):
  name,type,items
Rows with the same (name,type) are grouped; their `items` are aggregated (de-duplicated).

Examples:
  name,type,items
  Whitelist-ZCC,domains,domain1.com
  Whitelist-ZCC,domains,domain2.com
  Mike-DC,network,172.16.50.0/24
  Mike-DC,network,172.16.51.0/24

.env expected:
  ZTB_API_BASE="https://<tenant>-api.goairgap.com"
  BEARER="auto filled by ztb_login.py"
  API_KEY="CREATE IN UI"

Behavior:
  • If BEARER is missing at startup, we run ztb_login.py, reload .env, and continue.
  • If a request returns 401, we refresh once via ztb_login.py and retry automatically.
"""

from __future__ import annotations
import argparse
import csv
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from jinja2 import Environment, FileSystemLoader, StrictUndefined


# --- .env loading (dotenv first, tiny fallback second) -----------------------
def _tiny_load_env_file(path: str = ".env"):
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    _tiny_load_env_file(".env")
# ---------------------------------------------------------------------------


ROOT = Path(__file__).resolve().parent
LOGIN_SCRIPT = ROOT / "ztb_login.py"


def getenv_clean(key: str, default: str = "") -> str:
    val = os.getenv(key, default)
    return val.strip() if val else ""


def _normalize_base_root(raw: str) -> str:
    """Accept https://foo-api.goairgap.com[/api/v3|/api/v2] → return clean root"""
    base = (raw or "").strip().rstrip("/")
    if base.endswith("/api/v3") or base.endswith("/api/v2"):
        base = base.rsplit("/api/", 1)[0]
    return base


def _ensure_bearer_present_or_login():
    """If BEARER missing, invoke ztb_login.py to fetch it, then reload .env."""
    bearer = getenv_clean("BEARER")
    if bearer:
        return
    if not LOGIN_SCRIPT.exists():
        print("ERROR: BEARER not set and ztb_login.py not found. Please run login manually.", file=sys.stderr)
        sys.exit(1)
    print("🔐 BEARER missing — invoking ztb_login.py to obtain a fresh token…")
    try:
        subprocess.run([sys.executable, str(LOGIN_SCRIPT)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: ztb_login.py failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1)
    # reload env
    try:
        from dotenv import load_dotenv as _ld
        _ld(override=True)
    except Exception:
        _tiny_load_env_file(".env")


def _refresh_bearer_and_update_session(session: requests.Session) -> bool:
    """Invoke ztb_login.py, reload .env, and update Authorization header."""
    if not LOGIN_SCRIPT.exists():
        print("ERROR: Cannot refresh token automatically (ztb_login.py not found).", file=sys.stderr)
        return False
    print("🔄 401 Unauthorized — refreshing token via ztb_login.py and retrying once…")
    try:
        subprocess.run([sys.executable, str(LOGIN_SCRIPT)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: ztb_login.py failed with exit code {e.returncode}", file=sys.stderr)
        return False
    try:
        from dotenv import load_dotenv as _ld
        _ld(override=True)
    except Exception:
        _tiny_load_env_file(".env")
    new_bearer_raw = getenv_clean("BEARER")
    if not new_bearer_raw:
        print("ERROR: ztb_login.py ran but BEARER is still empty.", file=sys.stderr)
        return False
    session.headers["Authorization"] = f"Bearer {new_bearer_raw}"
    return True


def read_and_group(csv_path: Path) -> Dict[Tuple[str, str], Dict[str, object]]:
    """Group rows by (name,type); de-duplicate items per group."""
    groups: Dict[Tuple[str, str], Dict[str, object]] = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            try:
                name = (row["name"] or "").strip()
                typ = (row["type"] or "").strip().lower()
                item = (row["items"] or "").strip()
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

    # Ensure BEARER (may invoke ztb_login.py)
    _ensure_bearer_present_or_login()

    # ✅ Prefer ZTB_API_BASE for consistency with other tools
    base_url_env = getenv_clean("ZTB_API_BASE") or getenv_clean("BASE_URL")
    base_root = _normalize_base_root(base_url_env)
    if not base_root:
        print('❌ Missing ZTB_API_BASE or BASE_URL in .env (expected https://<tenant>-api.goairgap.com)', file=sys.stderr)
        sys.exit(1)

    bearer_raw = getenv_clean("BEARER")
    if not bearer_raw:
        print("❌ BEARER missing even after ztb_login.py. Aborting.", file=sys.stderr)
        sys.exit(1)

    API_V2 = f"{base_root}/api/v2"

    csv_path = Path(args.csv).resolve()
    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        sys.exit(1)

    template_path = Path(args.template).resolve()
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        sys.exit(1)

    groups = read_and_group(csv_path)
    if not groups:
        print("ℹ️  Nothing to do (no valid rows).")
        return

    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    tpl = env.get_template(template_path.name)

    # Create session
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {bearer_raw}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "objects_bulk.py",
    })

    def _request_with_auto_refresh(method: str, url: str, *, json_payload=None, timeout=45) -> requests.Response:
        r = session.request(method, url, json=json_payload, timeout=timeout)
        if r.status_code == 401:
            if _refresh_bearer_and_update_session(session):
                r = session.request(method, url, json=json_payload, timeout=timeout)
        return r

    url = f"{API_V2}/groups?refresh_token=enabled"
    created = skipped = errors = 0

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
            resp = _request_with_auto_refresh("POST", url, json_payload=payload)
            if resp.status_code in (200, 201, 202):
                created += 1
                if args.verbose:
                    print(f"✅ Created '{name}' ({typ})")
            elif resp.status_code == 409:
                print(f"⚠️  Exists (409): '{name}' ({typ}) — skipping")
                skipped += 1
            else:
                snippet = (resp.text or "")[:300].replace("\n", " ")
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