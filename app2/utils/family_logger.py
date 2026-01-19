import json, os
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def get_family_log_path(family_code: str):
    return os.path.join(LOG_DIR, f"family_{family_code}.json")


def init_family_log(family_code: str, family_name: str):
    path = get_family_log_path(family_code)
    if os.path.exists(path):
        return

    data = {
        "family_code": family_code,
        "family_name": family_name,
        "started_at": datetime.now().isoformat(),
        "purchases": [],
        "summary": {
            "total_attempt": 0,
            "total_success": 0,
            "total_failed": 0
        }
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
