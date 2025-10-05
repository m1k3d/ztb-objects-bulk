🛠️ ZTB Objects Bulk Creator

This automation tool is designed to rapidly deploy Zscaler ZTB objects — such as domain and network objects — in bulk, using simple CSV input and Jinja2 templates.
It mirrors the same API behavior as the ZTB UI but allows for scripted, repeatable, and large-scale onboarding.

⸻

✨ Key Capabilities
	•	Create Domain and Network objects directly through the API.
	•	Group and merge multiple rows by object name for cleaner data structures.
	•	Reference environment variables via .env for secure, reusable configuration.
	•	Use Jinja2 templates for payload rendering — easy to modify or extend for new object types.
	•	Built-in dry-run and debug modes for testing before live deployment.

⸻

📁 Directory Layout

Project root (ztb-objects-bulk/):
	•	objects_bulk.py — Main script to process CSV → generate payload → create ZTB objects.
	•	ztb_login.py — Authenticates with your tenant and retrieves a Bearer token, then loads it into your environment for all other scripts.
	•	templates/ — Folder containing your Jinja2 payload templates.
	•	object_payload.json.j2 — Default Jinja2 template used for object creation.
	•	objects.csv — CSV file defining objects to create (domains, networks, etc.).
	•	.env — Environment variables (tenant URL, API key, Bearer token).
	•	requirements.txt — Python dependencies.
	•	README.md — Documentation and usage guide.

Optional folders (recommended):
	•	logs/ — Store execution logs and debug outputs.
	•	examples/ — Example templates, payloads, or sample CSVs for reference.
	•	archive/ — Keep historical CSVs for version tracking.

⸻

⚙️ Environment Setup and Authentication

Before using any script, ensure your .env file is set up and that you’ve generated a valid Bearer token.

1️⃣ Configure Your .env File

At minimum, define:

ZIA_API_BASE="https://<tenant>-api.goairgap.com/api/v3"
API_KEY="<your_api_key>"
BEARER=""

2️⃣ Generate and Load Your Bearer Token

Use the included ztb_login.py helper.
This script handles the full login process automatically:

python3 ztb_login.py

It will:
	•	Call the ZTB API using your API key
	•	Write your token back into .env (e.g., BEARER="Bearer <token>")
	•	Print an export command so you can load it directly into your shell

3️⃣ Load the Environment Variables

Option A — Load all variables from .env:

set -a
source .env
set +a

Option B — Load only the BEARER token (quick mode):

eval "$(python3 ztb_login.py | tail -n1)"

This runs the export line automatically and updates your active shell session.

Next time, just run:

python3 ztb_login.py && set -a && source .env && set +a

or use the eval shortcut — you’ll be ready to deploy in seconds.

✅ Test Your Token

curl -s -H "Authorization: $BEARER" \
"$ZIA_API_BASE/api/v3/gateway?limit=1&refresh_token=enabled" | head

If you see JSON output instead of Unauthorized, your token is valid.

⸻

🧾 CSV Format

Example: objects.csv

name,type,fqdn,ip_prefix_local
Whitelist-ZCC,domains,domain1.com,
Whitelist-ZCC,domains,domain2.com,
Mike-DC,network,,172.16.50.0/24

	•	Rows with the same name are merged into a single object.
	•	Domains go under the fqdn column.
	•	Networks use the ip_prefix_local column.

⸻

🚀 Usage

Run the bulk creation script:

python3 objects_bulk.py

Arguments

Flag	Description
--csv <file>	Path to the input CSV (default: objects.csv)
--template <file>	Path to the Jinja2 template (default: templates/object_payload.json.j2)
--dry-run	Print payloads without posting to the API
--debug	Enable verbose API logging

Examples

# Run with default CSV
python3 objects_bulk.py

# Run with a custom CSV file
python3 objects_bulk.py --csv my_objects.csv

# Test payload generation only
python3 objects_bulk.py --dry-run


⸻

🧠 Notes & Best Practices
	•	Keep object names unique and consistent with your environment naming standards.
	•	Validate the first few rows using --dry-run before mass-creation.
	•	Store completed CSVs in /archive for rollback or audit tracking.
	•	Extend templates in /templates to add new fields or object types.

⸻

👤 Author
	•	Author: Mike Dechow (@m1k3d)
	•	Repo: github.com/m1k3d/ztb-site-automation
	•	License: MIT
