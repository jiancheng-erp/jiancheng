import requests
from app_config import WECHAT_TEST_MODE

def send_massage_to_users(message, users="SunHaoZheng"):
    if WECHAT_TEST_MODE:
        # In test mode, we use a different URL for sending messages.
        users = "SunHaoZheng"
    url = f"http://121.43.33.97:8067/send_wechat"
    payload = {
        "content": message,
        "touser": "SunHaoZheng|" + users
    }
    response = requests.post(url, json=payload)
    return response.json()
    