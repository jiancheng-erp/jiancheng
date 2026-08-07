import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
from config import config

TEMPLATE_STORE = Path(__file__).with_name("wechat_templates.json")

# 企业微信群机器人 webhook 地址
GROUP_WEBHOOK_URL = (
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
    "?key=4748cee1-02c9-4867-bbe0-dffbdbd1cf3f"
)


def send_message_to_group(message, webhook_url=GROUP_WEBHOOK_URL):
    """通过群机器人 webhook 向企业微信群推送文本消息。"""
    payload = {"msgtype": "text", "text": {"content": message}}
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.json()
    except Exception as exc:
        return {"errcode": -1, "errmsg": str(exc)}


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


def send_massage_to_users(message, users="SunHaoZheng", push_to_group=False):
    if config.WECHAT_TEST_MODE:
        # In test mode, we use a different URL for sending messages.
        users = "SunHaoZheng"
    # 下发、退回类消息（push_to_group=True）统一带上具体时间
    if push_to_group:
        message = f"{message}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    url = f"http://121.43.33.97:8067/send_wechat"
    payload = {"content": message, "touser": "SunHaoZheng|" + users}
    response = requests.post(url, json=payload)
    # 仅在需要时（如下发、退回消息）向企业微信群推送，定时通知不推送到群；测试模式不推送到群
    if push_to_group and not config.WECHAT_TEST_MODE:
        send_message_to_group(message)
    return response.json()


def send_configurable_message(
    template_key: str,
    default_content: str,
    default_users: str,
    context: Optional[Dict] = None,
    push_to_group: bool = False,
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
    return send_massage_to_users(rendered_content, users, push_to_group=push_to_group)
