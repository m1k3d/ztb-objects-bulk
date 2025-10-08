# objects_bulk.py — Bulk create ZTB Objects from CSV

Create ZTB Objects (Domains / Network CIDRs) in bulk from a CSV.  
Rows with the same (name, type) are grouped and their items are aggregated & de-duplicated.

---

## ⚙️ Requirements

- Python 3.9+
- requests, jinja2 (install via `pip install -r requirements.txt` if needed)

---

## 🔐 Auth & Environment

Create a `.env` file in the repo root:

```bash
ZTB_API_BASE="https://<tenant>-api.goairgap.com"
BEARER="auto filled by ztb_login.py"
API_KEY="CREATE IN UI"

How it works now
	•	If BEARER is missing, the script automatically runs ztb_login.py, reloads .env, and continues.
	•	If any API call returns 401, it visibly refreshes via ztb_login.py and retries once.
	•	No need to export env vars in your shell or use set -a / source .env.

Note: ZTB_API_BASE should be the root tenant URL (no /api/v2 or /api/v3 suffix).
ztb_login.py uses your API_KEY to fetch a fresh bearer token and writes it to .env.

⸻

📄 CSV Format

Headers are required:

name,type,items
Whitelist-ZCC,domains,domain1.com
Whitelist-ZCC,domains,domain2.com
Mike-DC,network,172.16.50.0/24
Mike-DC,network,172.16.51.0/24

	•	type supports: domains or network
	•	Rows with the same (name, type) get merged; items are automatically de-duplicated.

⸻

🧩 Template

By default, payloads are rendered using:

templates/object_payload.json.j2

You can customize this template to match your tenant’s schema or extend it with additional object fields.

⸻

🚀 Usage

# Dry run (print payloads, don't POST)
python3 objects_bulk.py --dry-run

# Standard run
python3 objects_bulk.py

# Verbose output (shows payloads and responses)
python3 objects_bulk.py -v

# Use a different CSV
python3 objects_bulk.py --csv my_objects.csv

# Use a custom template
python3 objects_bulk.py --template templates/custom_object_payload.json.j2


⸻

✅ Behavior
	•	Groups rows by (name, type) and aggregates unique items
	•	Builds payloads via Jinja2 template
	•	POSTs to /api/v2/groups?refresh_token=enabled
	•	Handles common responses:
	•	200/201 → ✅ Created
	•	409 → ⚠️ Already exists (skipped)
	•	Summarizes results (Created / Skipped / Errors)

⸻

🧯 Troubleshooting

Issue	Fix
401 Unauthorized loop	Check API_KEY validity in .env and ensure ztb_login.py exists.
404 or bad base URL	Confirm ZTB_API_BASE uses the root domain (no /api/v2 or /api/v3).
Template render errors	The Jinja environment is strict — fix missing variables or CSV headers.


⸻

🆕 What’s New
	•	🪄 Auto-login + token refresh on 401 (no manual steps)
	•	⚙️ .env loader integration (no set -a required)
	•	💡 Clean error handling & summary
	•	🧩 Automatic CSV grouping + de-dupe
	•	🧠 Future support planned for Ports, Zones, and additional object types

---