import os
import json
from datetime import datetime
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SYNTHETIC_DATA = {
    "company_faqs": {
        "content": (
            "### Company Overview & FAQ Portal\n\n"
            "Welcome to the internal knowledge base. Here are the core guidelines for the team:\n\n"
            "Q: What are the official working hours and hybrid policies?\n"
            "A: Our core hours are 8:30 AM to 3:30 PM. We follow a hybrid model where teams "
            "gather in-office on every other day except wednesdays or thursdays. Remote work is optional on either days.Leave is on every saturdays and sundays\n\n"
            "Q: How do I submit an expense report for project components?\n"
            "A: All receipts must be uploaded to the internal dashboard under the 'Finance' tab "
            "by the last Friday of each week."
        ),
        "metadata": {
            "title": "Company Overview and Team FAQs",
            "tags": ["hr", "faq", "policy", "onboarding"],
            "type": "documentation",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    },
    "tech_tutorials": {
        "content": (
            "### Technical Tutorial: Building Independent API Connections\n\n"
            "When integrating internal tools with our backend management gateway, developers must pass "
            "the secure system token within the HTTP authorization header layout.\n\n"
            "Python Gateway Verification Snippet:\n"
            "```python\n"
            "import requests\n\n"
            "headers = {\n"
            "    'Authorization': 'Bearer SYS_SECURE_TOKEN_2026',\n"
            "    'Content-Type': 'application/json'\n"
            "}\n"
            "response = requests.get('[https://api.internal/v1/status](https://api.internal/v1/status)', headers=headers)\n"
            "print(f'Gateway Connection Status: {response.status_code}')\n"
            "```"
        ),
        "metadata": {
            "title": "Technical Tutorials and API Snippets",
            "tags": ["backend", "api", "python", "developer"],
            "type": "tutorial",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    },
    "sops_best_practices": {
        "content": (
            "### Standard Operating Procedure: Safe Production Deployments\n\n"
            "Document ID: SOP-ENG-042\n"
            "Strict adherence to these deployment parameters is mandatory for all engineering tracks:\n\n"
            "1. Code Freeze Windows: Direct merging or deployment targeting pipeline environments "
            "is strictly frozen after 3:50 PM on Fridays to guarantee system weekend stability.\n"
            "2. Mandatory Peer Review: No pull request may pass to production staging without a "
            "minimum of two independent approvals from senior architecture leads.\n"
            "3. Testing Coverage: Comprehensive automated testing runs must pass with 100% success rate."
        ),
        "metadata": {
            "title": "SOPs and Internal Best Practices",
            "tags": ["devops", "sop", "security", "deployment"],
            "type": "standard_operating_procedure",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    }
}

def run_generation_pipeline():
    print("==========================================")
    print(" Running Synthetic Data Generation Engine ")
    print("==========================================\n")
    
    for theme_folder, payload in SYNTHETIC_DATA.items():
        target_path = os.path.join(DATA_DIR, theme_folder)
        os.makedirs(target_path, exist_ok=True)
        content_file = os.path.join(target_path, "document.txt")
        metadata_file = os.path.join(target_path, "metadata.json")
        with open(content_file, "w", encoding="utf-8") as txt_out:
            txt_out.write(payload["content"])
        with open(metadata_file, "w", encoding="utf-8") as json_out:
            json.dump(payload["metadata"], json_out, indent=4)
        print(f"[SUCCESS] Generated theme vault inside: data/{theme_folder}/")
        print(f"   ├── Saved text content to document.txt")
        print(f"   └── Saved structural data to metadata.json")
        print("-" * 50)
    print("\n✅ Synthetic Data Matrix fully deployed to disk!")

if __name__ == "__main__":
    run_generation_pipeline()