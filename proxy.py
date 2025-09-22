from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ==== Cấu hình tài khoản UDC ====
UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
UDC_DATA_URL = "https://udc.vrain.vn/api/private/v1/organizations/details"

USERNAME = os.getenv("UDC_USERNAME", "udchcm")        # thay bằng tài khoản thật hoặc set ENV trên Render
PASSWORD = os.getenv("UDC_PASSWORD", "123456")
ORG_UUID = os.getenv("UDC_ORGUUID", "b147bbcd-0371-4cab-9052-151660e86ea5")


def login_udc():
    """Đăng nhập UDC và lấy cookie sid"""
    try:
        resp = requests.post(
            UDC_LOGIN_URL,
            json={
                "username": USERNAME,
                "password": PASSWORD,
                "orgUuid": ORG_UUID
            },
            timeout=10
        )
        if resp.status_code == 200:
            sid = resp.cookies.get("sid")
            return sid
        else:
            print("Login thất bại:", resp.text)
            return None
    except Exception as e:
        print("Lỗi login:", e)
        return None


def fetch_udc_data(from_time, to_time, interval="_10m"):
    """Gọi API lấy dữ liệu mưa sau khi login"""
    sid = login_udc()
    if not sid:
        return {"error": "Không login được UDC"}

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
        "i": interval,
        "stationGroups": []
    }

    try:
        resp = requests.post(UDC_DATA_URL, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"Lỗi {resp.status_code}", "message": resp.text}
    except Exception as e:
        return {"error": "Exception khi fetch data", "message": str(e)}


@app.route("/")
def home():
    return jsonify({"status": "ok", "message": "Proxy UDC running"})


@app.route("/getdata", methods=["POST"])
def get_data():
    try:
        data = request.get_json()
        from_time = data.get("from", "2025-09-19 00:00:00")
        to_time = data.get("to", "2025-09-19 23:59:59")
        interval = data.get("i", "_10m")

        result = fetch_udc_data(from_time, to_time, interval)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Lỗi trong proxy", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
