from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 企业微信配置
CORPID = "ww3e0b094fbf683081"
CORPSECRET = "WYQx5-ukXEBW-vvnNvqCBXTIoaLZQRF2xcOuWMJI_fE"
AGENTID = "1000002"  # 应用的AgentID

# 获取 access_token
def get_access_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORPID}&corpsecret={CORPSECRET}"
    response = requests.get(url)
    data = response.json()
    if data.get('errcode') == 0:
        return data['access_token']
    else:
        raise Exception(data.get('errmsg'))

# 发送消息
def send_text_message(touser, content):
    access_token = get_access_token()
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "touser": touser,              # 用户ID，可以多个 "user1|user2"
        "msgtype": "text",
        "agentid": AGENTID,
        "text": {
            "content": content
        },
        "safe": 0
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

# 接收 ERP 请求的接口
@app.route('/send_wechat', methods=['POST'])
def send_wechat():
    try:
        data = request.json
        touser = data.get("touser")         # 期望格式: "SunHaoZheng" 或 "User1|User2"
        content = data.get("content")       # 发送的内容

        if not touser or not content:
            return jsonify({"status": "error", "msg": "Missing touser or content"}), 400

        result = send_text_message(touser, content)
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8067, debug=True)