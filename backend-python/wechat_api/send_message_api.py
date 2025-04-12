import requests

def send_massage_to_users(message, users="SunHaoZheng"):
    url = f"http://121.43.33.97:8067/send_wechat"
    payload = {
        "content": message,
        "touser": users
    }
    response = requests.post(url, json=payload)
    return response.json()
    