import json
import os
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


def log_family_purchase(
    family_code: str,
    purchase_no: int,
    variant: str,
    option: str,
    price: int,
    response: dict | None = None,
    exception: Exception | None = None
):
    path = get_family_log_path(family_code)

    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    status = "SUCCESS" if response and response.get("status") == "SUCCESS" else "FAILED"

    entry = {
        "no": purchase_no,
        "variant": variant,
        "option": option,
        "price": price,
        "status": status,
        "response": response if response else {
            "exception": str(exception)
        }
    }

    data["purchases"].append(entry)
    data["summary"]["total_attempt"] += 1

    if status == "SUCCESS":
        data["summary"]["total_success"] += 1
    else:
        data["summary"]["total_failed"] += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
