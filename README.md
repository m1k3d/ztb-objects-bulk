🧠 ZTB Objects Bulk Creator

Automate the creation of Zscaler ZTB objects (domains, networks, etc.) — API-driven, scalable, and template-powered.

Author: Mike Dechow (@m1k3d)
Repo: github.com/m1k3d/ztb-site-automation
License: MIT
Version: 1.0.0

⸻

🚀 Overview

This automation suite is designed to rapidly deploy Zscaler ZTB objects — including domains and network prefixes — using a CSV-driven workflow.
It mirrors the same behavior and API calls used by the ZTB UI, but at enterprise scale.

✨ Key Capabilities
- **Bulk create ZTB objects such as Domains and Network prefixes.
- **Group rows by object name for clean, aggregated payloads.
- **Supports multiple object types, including domain-based and IP-based entries.
- **Environment-driven authentication using .env (tenant API URL, API key, Bearer token).
- **Template-based payloads using Jinja2 for flexibility and reuse.
- **Dry-run and Debug modes for validation before live deployment.
- **Integrated bearer token helper — one-line script to fetch and export credentials.

⸻

🧩 Directory Layout

Project root (ztb-objects-bulk/):
- objects_bulk.py — Main script to process CSV → generate payload → create ZTB objects.
- ztb_login.py — Authenticates and exports the BEARER token automatically to .env.
- templates/ — Folder containing Jinja2 payload templates.
- object_payload.json.j2 — Jinja2 object creation template (used by objects_bulk.py).
- objects.csv — CSV with definitions for domain or network objects.
- .env — Environment variables (tenant API URL, BEARER token, and API key).

Optional folders (recommended):
- logs/ — Stores execution logs, debug traces, and run summaries.
- archive/ — Keeps historical CSVs for version tracking.
- examples/ — Contains sample templates, CSVs, and payload examples for reference.
⸻

⚙️ Before You Begin

Before using the automation, set up your environment and API credentials.

1️⃣ Configure Environment Variables (.env)

Create a file named .env in the repo root:

ZIA_API_BASE="https://<tenant>-api.goairgap.com/api/v3"
API_KEY="<your_api_key>"
BEARER=""


⸻

2️⃣ Generate and Load Your Bearer Token

Use the included helper script to handle login automatically:

python3 ztb_login.py

This will:
- Call the ZTB API using your API key.
- Write the Bearer token back into .env (e.g., BEARER="Bearer <token>").
- Print an export command so you can load it directly into your shell.

You can also fetch and load everything at once:

python3 ztb_login.py && set -a && source .env && set +a

Tip: The login helper uses your existing .env credentials and auto-updates the token on each run.

⸻

3️⃣ Verify the Bearer Token

Confirm the token works by running:

curl -s -H "Authorization: $BEARER" \
"$ZIA_API_BASE/api/v3/gateway?limit=1&refresh_token=enabled" | head

If you see JSON output (not “Unauthorized”), you’re authenticated successfully.

⸻

🧾 CSV Format

Example (objects.csv):

name,type,fqdn,ip_prefix_local
Whitelist-ZCC,domains,domain1.com,
Whitelist-ZCC,domains,domain2.com,
Mike-DC,network,,172.16.50.0/24

- **name — Object name (rows with the same name are grouped).
- **type — Either domains or network.
- **fqdn — Domain entries for type domains.
- **ip_prefix_local — Subnet prefixes for type network.
⸻

🧱 Running the Automation

Dry Run (Validation Only):

python3 objects_bulk.py --dry-run

Full Deployment:

python3 objects_bulk.py

Debug Mode (verbose output):

python3 objects_bulk.py --debug

Arguments:

Flag	Description
--csv <file>	Path to input CSV (default: objects.csv)
--template <file>	Jinja2 template path (default: templates/object_payload.json.j2)
--dry-run	Renders payloads without sending to API
--debug	Prints detailed API requests/responses


⸻

🧩 File Reference

File	Description
objects_bulk.py	Creates ZTB objects from CSV definitions
ztb_login.py	Retrieves API bearer token automatically
object_payload.json.j2	Jinja2 payload template for object creation
objects.csv	CSV defining domains and networks
.env	Tenant API configuration
requirements.txt	Python dependencies
examples/	Sample payloads and templates


⸻

💡 Best Practices

✅ Validate your CSV with --dry-run before bulk posting.
✅ Use consistent naming for object groups (e.g., Whitelist-*, Site-DC-*).
✅ Keep .env and API keys out of version control.
✅ Archive successful CSVs under /archive for audit history.
✅ Extend Jinja2 templates for custom fields or new object types.

⸻

🧠 Example Workflow Summary

1️⃣ Prepare .env with tenant URL, API key, and blank BEARER field.
2️⃣ Run ztb_login.py to fetch and export your BEARER token.
3️⃣ Build or import objects.csv with your objects to deploy.
4️⃣ Run objects_bulk.py --dry-run to validate payloads.
5️⃣ Run objects_bulk.py to push to API.
6️⃣ Verify in ZTB UI — confirm new objects appear under Object Management.

⸻

🧰 Troubleshooting Tips

Symptom	Likely Cause	Fix
401 Unauthorized	Expired or missing Bearer token	Re-run ztb_login.py
Bad Request (400)	Missing or invalid CSV column	Check type, fqdn, or ip_prefix_local fields
Empty Object Group	Same object name but mismatched types	Use consistent type per group
API Timeout	Too many objects in a single request	Split CSV into smaller chunks


⸻

🧭 License

This project is licensed under the MIT License — feel free to modify and extend it for your own organization.

⸻