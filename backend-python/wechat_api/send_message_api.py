import json
from pathlib import Path
from typing import Dict, Optional

import requests
from app_config import WECHAT_TEST_MODE

TEMPLATE_STORE = Path(__file__).with_name("wechat_templates.json")


def _load_templates() -> Dict[str, Dict]:
    if TEMPLATE_STORE.exists():
        with TEMPLATE_STORE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_templates(payload: Dict[str, Dict]) -> None:
    TEMPLATE_STORE.parent.mkdir(parents=True, exist_ok=True)
    with TEMPLATE_STORE.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def upsert_template(key: str, content: str, users: str, description: str = "") -> Dict:
    templates = _load_templates()
    templates[key] = {
        "content": content,
        "users": users,
        "description": description,
    }
    _save_templates(templates)
    return templates[key]


def list_templates() -> Dict[str, Dict]:
    return _load_templates()


def delete_template(key: str) -> bool:
    templates = _load_templates()
    if key in templates:
        templates.pop(key)
        _save_templates(templates)
        return True
    return False


def _render(content: str, context: Optional[Dict] = None) -> str:
    try:
        return content.format(**(context or {}))
    except Exception:
        return content


def send_massage_to_users(message, users="SunHaoZheng"):
    if WECHAT_TEST_MODE:
        # In test mode, we use a different URL for sending messages.
        users = "SunHaoZheng"
    url = f"http://121.43.33.97:8067/send_wechat"
    payload = {"content": message, "touser": "SunHaoZheng|" + users}
    response = requests.post(url, json=payload)
    return response.json()


def send_configurable_message(
    template_key: str,
    default_content: str,
    default_users: str,
    context: Optional[Dict] = None,
) -> Dict:
    """
    Send a message using a configurable template. If the template is missing, fall back to the provided defaults.
    """
    templates = _load_templates()
    template = templates.get(
        template_key,
        {"content": default_content, "users": default_users},
    )
    rendered_content = _render(template.get("content", default_content), context)
    users = template.get("users", default_users)
    return send_massage_to_users(rendered_content, users)
