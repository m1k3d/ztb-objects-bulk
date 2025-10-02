Got it 👍 Let’s scrap the merge mess and just give you a clean, ready-to-paste README.md that you can copy into either GitHub’s web editor or VS Code.

Here’s a fresh one:

# 🚀 ZTB Objects Bulk Creator

This tool automates the creation of Zscaler Zero Trust Branch (ZTB) objects (e.g., **domains** or **network prefixes**) in bulk using:

- **CSV input** for object data  
- **Jinja2 templates** for payload generation  
- **Python requests** for posting to the Zscaler API  

It’s designed to save time when onboarding large numbers of objects into ZTB without manually clicking through the UI.

---

## ✨ Features
- Supports **domain objects** (`type: domains`) and **network objects** (`type: network`).
- Groups rows by **name** so multiple domains or subnets can be aggregated into one object.
- Uses a `.env` file for credentials and API base URL.
- Modular design: extendable templates for new object types.

---

## 📂 Project Structure

ztb-objects-bulk/
├── templates/
│   └── object_payload.json.j2     # Jinja2 template for object payload
├── objects_bulk.py                # Main script (reads CSV -> groups -> POSTs)
├── objects.csv                    # Example CSV input
├── .env.example                   # Sample env file (copy to .env)
├── requirements.txt               # Python dependencies
└── README.md                      # This file

---

## ⚙️ Setup

1. Clone the repo:
```bash
git clone https://github.com/<your-username>/ztb-objects-bulk.git
cd ztb-objects-bulk

	2.	Install dependencies:

pip install -r requirements.txt

	3.	Create .env with:

ZIA_API_BASE="https://<tenant>-api.goairgap.com/api/v3"
BEARER="<your_bearer_token>"

	4.	Load into your shell:

export $(grep -v '^#' .env | xargs)

	5.	Quick token check:

curl -s -H "Authorization: Bearer $BEARER" \
"$ZIA_API_BASE/Gateway/?limit=1&refresh_token=enabled" | jq


⸻

📑 CSV Format

Example: objects.csv

name,type,fqdn,ip_prefix_local
Whitelist-ZCC,domains,domain1.com,
Whitelist-ZCC,domains,domain2.com,
Mike-DC,network,,172.16.50.0/24


⸻

▶️ Run

python3 objects_bulk.py


⸻

📦 Example Payloads

Domain Object

{
  "name": "Whitelist-ZCC",
  "type": "domains",
  "owner": "user",
  "autonomous": false,
  "member_attributes": {
    "fqdn": ["domain1.com", "domain2.com"]
  }
}

Network Object

{
  "name": "Mike-DC",
  "type": "network",
  "owner": "user",
  "autonomous": false,
  "member_attributes": {
    "ip_prefix_local": ["172.16.50.0/24"]
  }
}


