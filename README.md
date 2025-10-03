# 🛠️ ZTB Objects Bulk Creator

This tool automates the creation of **Zscaler Zero Trust Branch (ZTB)** objects (e.g., domains or network prefixes) in bulk using:

- **CSV input** for object data  
- **Jinja2 templates** for payload generation  
- **Python requests** for posting to the Zscaler API  

It’s designed to save time when onboarding large numbers of objects into ZTB without manually clicking through the UI.  

---

## ✨ Features

- Supports **domain objects** (`type: domains`) and **network objects** (`type: network`).  
- Groups rows by **name**, so multiple domains or subnets are aggregated into one object.  
- Uses a `.env` file for credentials and API base URL.  
- Modular design: easily extendable templates for new object types.  

---

## 📂 Project Structure

- `templates/` → contains Jinja2 payload templates  
- `object_payload.json.j2` → Jinja2 template for object payload  
- `objects_bulk.py` → main script (reads CSV → groups → POSTs to API)  
- `objects.csv` → sample CSV input file (domains/networks)  
- `.env.example` → example env file (copy and rename to `.env`)  
- `requirements.txt` → Python dependencies  
- `README.md` → this documentation  

---

## ⚙️ Setup

### 🔑 Authentication & Environment Setup

Before running any automation scripts, you need a valid bearer token. This repo includes a helper script: ztb_login.py.

1. Configure your .env

At minimum, set the following:

ZIA_API_BASE=https://<tenant>-api.goairgap.com/api/v3
API_KEY=<your_api_key>
BEARER=""

2. Generate a Bearer Token

Run the login helper:

python3 ztb_login.py

This will:
	•	Call the ZTB API with your API key
	•	Write the BEARER="Bearer <delegate_token>" value into your .env
	•	Print an export BEARER=... line for convenience

3. Load the Environment Variables

You have two options:

Option A — Load everything from .env

set -a
source .env
set +a

This makes all variables (ZIA_API_BASE, API_KEY, BEARER, etc.) available in your shell.

Option B — Load just the BEARER token

eval "$(python3 ztb_login.py | tail -n1)"

This executes the printed export BEARER=... line from the script, updating your shell with only the new bearer token.

4. Test Your Token

Confirm it works:

curl -s -H "Authorization: $BEARER" \
  "$ZIA_API_BASE/api/v3/gateway?limit=1&refresh_tokenenabled=" | head

If you see JSON output instead of Unauthorized, your token is valid.

👉 Next time, you just run:

python3 ztb_login.py && set -a && source .env && set +a

or use the eval shortcut, and you’re good to go.

⸻

### 📑 CSV Format

Example objects.csv:

name,type,fqdn,ip_prefix_local
Whitelist-ZCC,domains,domain1.com,
Whitelist-ZCC,domains,domain2.com,
Mike-DC,network,,172.16.50.0/24

	•	Rows with the same name are merged into a single object.
	•	Domains go into fqdn column, networks into ip_prefix_local.

⸻

### 🚀 Usage

Run the bulk creation script:

python3 objects_bulk.py

Arguments
	•	--csv <file> → Path to input CSV (default: objects.csv)
	•	--template <file> → Path to Jinja2 template (default: templates/object_payload.json.j2)
	•	--dry-run → Prints payloads without sending to API
	•	--debug → Verbose logging for troubleshooting

Examples:

# Run with default CSV
python3 objects_bulk.py

# Run with custom CSV
python3 objects_bulk.py --csv my_objects.csv

# Test payload generation only
python3 objects_bulk.py --dry-run


⸻


👤 Author
	•	Author: Mike Dechow (@m1k3d)
	•	Repo: github.com/m1k3d/ztb-site-automation
	•	License: MIT

