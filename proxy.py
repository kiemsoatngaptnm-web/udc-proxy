from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
DETAILS_URL = "https://udc.vrain.vn/api/private/v1/organizations/details"
ORG_UUID = "b147bbcd-0371-4cab-9052-151660e86ea5"

@app.route("/")
def home():
    return {"status": "ok", "message": "Proxy running"}

@app.route("/getdata", methods=["POST"])
def get_data():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    from_time = data.get("from")
    to_time = data.get("to")

    # 1. Đăng nhập để lấy cookie sid
    login_payload = {
        "username": username,
        "password": password,
        "orgUuid": ORG_UUID
    }
    login = requests.post(LOGIN_URL, json=login_payload)
    if "sid" not in login.cookies:
        return jsonify({"error": "Login failed", "response": login.text}), 401
    sid = login.cookies["sid"]

    # 2. Gọi API details với sid
    headers = {
        "Content-Type": "application/json",
        "x-org-uuid": ORG_UUID,
        "Cookie": f"sid={sid}"
    }
    payload = {
        "fromHour": None,
        "from": from_time,
        "toHour": None,
        "to": to_time,
        "i": "_10m",
        "stationGroups": []
    }
    r = requests.post(DETAILS_URL, headers=headers, json=payload)
    return jsonify(r.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
