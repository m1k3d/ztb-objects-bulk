# ZTB Objects Bulk Creator

This tool automates the creation of Zscaler Zero Trust Branch (ZTB) objects (e.g. **domains** or **network prefixes**) in bulk using:
- **CSV input** for object data  
- **Jinja2 templates** for payload generation  
- **Python requests** for posting to the Zscaler API  

It’s designed to save time when onboarding large numbers of objects into ZTB without manually clicking through the UI.

---

## 🚀 Features
- Supports **domain objects** (`type: domains`) and **network objects** (`type: network`).
- Groups rows by **name** so multiple domains or subnets can be aggregated into one object.
- Uses `.env` file for credentials and API base URL.
- Built with modularity: you can easily extend templates for new object types.

---

## 📂 Project Structure

ztb-objects-bulk/
├─ templates/
│  └─ object_payload.json.j2       # Jinja2 template for object payload
├─ objects_bulk.py                 # Main script (reads CSV -> groups -> POSTs)
├─ objects.csv                     # Example CSV input
├─ .env.example                    # Sample env file (copy to .env)
├─ requirements.txt                # Python deps
└─ README.md

---

## ⚙️ Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/<your-username>/ztb-objects-bulk.git
   cd ztb-objects-bulk

	2.	Install dependencies:

pip install -r requirements.txt


	3.	Create your .env file (copy from .env.example) and fill in:

BASE_URL=https://<your-tenant>-api.goairgap.com
API_TOKEN=<your-api-token-or-bearer>



⸻

📝 CSV Format

Example: objects.csv

name	type	fqdn	ip_prefix_local
Whitelist-ZCC	domains	domain1.com	
Whitelist-ZCC	domains	domain2.com	
Mike-DC	network		172.16.50.0/24

👉 Rows with the same name will be combined into a single object.

⸻

▶️ Run

python3 objects_bulk.py


⸻

🛠️ Example Payloads

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


⸻

🧹 .gitignore

Add a .gitignore so secrets and junk don’t get pushed:

.env
__pycache__/
*.pyc
.DS_Store


⸻

📌 Notes
	•	This script requires an API token with permission to create objects in ZTB.
	•	If an object with the same name already exists, the API will return an error (you can extend logic later to skip or update instead).
	•	Extend the Jinja2 template (templates/object_payload.json.j2) to add new object types.

⸻

📄 License

MIT

