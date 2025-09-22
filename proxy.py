# from flask import Flask, request, jsonify
# import requests
# import os

# app = Flask(__name__)

# # ==== Cấu hình tài khoản UDC ====
# UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
# UDC_DATA_URL = "https://udc.vrain.vn/api/private/v1/organizations/details"

# USERNAME = os.getenv("UDC_USERNAME", "udchcm")        # thay bằng tài khoản thật hoặc set ENV trên Render
# PASSWORD = os.getenv("UDC_PASSWORD", "123456")
# ORG_UUID = os.getenv("UDC_ORGUUID", "b147bbcd-0371-4cab-9052-151660e86ea5")


# def login_udc():
#     """Đăng nhập UDC và lấy cookie sid"""
#     try:
#         resp = requests.post(
#             UDC_LOGIN_URL,
#             json={
#                 "username": USERNAME,
#                 "password": PASSWORD,
#                 "orgUuid": ORG_UUID
#             },
#             timeout=10
#         )
#         if resp.status_code == 200:
#             sid = resp.cookies.get("sid")
#             return sid
#         else:
#             print("Login thất bại:", resp.text)
#             return None
#     except Exception as e:
#         print("Lỗi login:", e)
#         return None


# def fetch_udc_data(from_time, to_time, interval="_10m"):
#     """Gọi API lấy dữ liệu mưa sau khi login"""
#     sid = login_udc()
#     if not sid:
#         return {"error": "Không login được UDC"}

#     headers = {
#         "Content-Type": "application/json",
#         "x-org-uuid": ORG_UUID,
#         "Cookie": f"sid={sid}"
#     }
#     payload = {
#         "fromHour": None,
#         "from": from_time,
#         "toHour": None,
#         "to": to_time,
#         "i": interval,
#         "stationGroups": []
#     }

#     try:
#         resp = requests.post(UDC_DATA_URL, headers=headers, json=payload, timeout=15)
#         if resp.status_code == 200:
#             return resp.json()
#         else:
#             return {"error": f"Lỗi {resp.status_code}", "message": resp.text}
#     except Exception as e:
#         return {"error": "Exception khi fetch data", "message": str(e)}


# @app.route("/")
# def home():
#     return jsonify({"status": "ok", "message": "Proxy UDC running"})


# @app.route("/getdata", methods=["POST"])
# def get_data():
#     try:
#         data = request.get_json()
#         from_time = data.get("from", "2025-09-19 00:00:00")
#         to_time = data.get("to", "2025-09-19 23:59:59")
#         interval = data.get("i", "_10m")

#         result = fetch_udc_data(from_time, to_time, interval)
#         return jsonify(result)
#     except Exception as e:
#         return jsonify({"error": "Lỗi trong proxy", "message": str(e)}), 500


# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)

# # app.py
# from flask import Flask, request, jsonify
# import requests

# app = Flask(__name__)

# UDC_API_BASE = "https://udc.vrain.vn/api/private/v1"

# # Hàm lấy token UDC
# def get_udc_token(username="udchcm", password="123456"):
#     url = f"{UDC_API_BASE}/auth/login"
#     payload = {"username": username, "password": password}
#     resp = requests.post(url, json=payload)
#     resp.raise_for_status()
#     return resp.json().get("token")

# @app.route("/")
# def home():
#     return {"status": "ok", "msg": "Flask chạy trên Render thành công 🎉"}

# @app.route("/udc-data")
# def udc_data():
#     """Ví dụ: /udc-data?from=2025-09-21%2000:00:00&to=2025-09-21%2023:59:59&service=ktt"""
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     service = request.args.get("service", "ktt")

#     try:
#         token = get_udc_token()
#         headers = {"Authorization": f"Bearer {token}"}
#         url = f"{UDC_API_BASE}/intervals?from={from_time}&to={to_time}&service={service}"
#         resp = requests.get(url, headers=headers)
#         resp.raise_for_status()
#         return jsonify(resp.json())
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# from flask import Flask, request, jsonify, render_template_string
# import requests

# app = Flask(__name__)

# UDC_API_BASE = "https://udc.vrain.vn/api/private/v1"

# # Hàm lấy token
# def get_udc_token(username="udchcm", password="123456"):
#     url = f"{UDC_API_BASE}/auth/login"
#     payload = {"username": username, "password": password}
#     resp = requests.post(url, json=payload)
#     resp.raise_for_status()
#     return resp.json().get("token")

# @app.route("/")
# def home():
#     return {"status": "ok", "msg": "Flask API chạy trên Render"}

# @app.route("/udc-data")
# def udc_data():
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     service = request.args.get("service", "ktt")

#     try:
#         token = get_udc_token()
#         headers = {"Authorization": f"Bearer {token}"}
#         url = f"{UDC_API_BASE}/intervals?from={from_time}&to={to_time}&service={service}"
#         resp = requests.get(url, headers=headers)
#         resp.raise_for_status()
#         return jsonify(resp.json())
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# # 📊 Dashboard HTML
# @app.route("/dashboard")
# def dashboard():
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     service = request.args.get("service", "ktt")

#     try:
#         token = get_udc_token()
#         headers = {"Authorization": f"Bearer {token}"}
#         url = f"{UDC_API_BASE}/intervals?from={from_time}&to={to_time}&service={service}"
#         resp = requests.get(url, headers=headers)
#         resp.raise_for_status()
#         data = resp.json()

#         # HTML template đơn giản
#         template = """
#         <!DOCTYPE html>
#         <html>
#         <head>
#             <title>Bảng dữ liệu UDC</title>
#             <style>
#                 body { font-family: Arial, sans-serif; padding: 20px; }
#                 table { border-collapse: collapse; width: 100%; }
#                 th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
#                 th { background-color: #4CAF50; color: white; }
#                 tr:nth-child(even) { background-color: #f2f2f2; }
#             </style>
#         </head>
#         <body>
#             <h2>Dữ liệu UDC ({{ from_time }} → {{ to_time }})</h2>
#             <table>
#                 <thead>
#                     <tr>
#                         {% for col in data[0].keys() %}
#                             <th>{{ col }}</th>
#                         {% endfor %}
#                     </tr>
#                 </thead>
#                 <tbody>
#                     {% for row in data %}
#                         <tr>
#                             {% for val in row.values() %}
#                                 <td>{{ val }}</td>
#                             {% endfor %}
#                         </tr>
#                     {% endfor %}
#                 </tbody>
#             </table>
#         </body>
#         </html>
#         """
#         return render_template_string(template, data=data, from_time=from_time, to_time=to_time)

#     except Exception as e:
#         return f"<h3 style='color:red'>Lỗi: {e}</h3>"

# proxy.py
from flask import Flask, request, jsonify
import requests
import time
import logging

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# ---------- CẤU HÌNH ----------
UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
UDC_API_DETAILS = "https://udc.vrain.vn/api/private/v1/organizations/details"

# Thay bằng tài khoản thực tế
USERNAME = "udchcm"
PASSWORD = "123456"
ORG_UUID = "b147bbcd-0371-4cab-9052-151660e86ea5"

# Session toàn cục để giữ cookie sid
session = requests.Session()
last_login_ts = 0
# --------------------------------

def login_udc(force=False):
    global last_login_ts, session

    # tránh login quá thường (10 phút)
    if not force and time.time() - last_login_ts < 600:
        if session.cookies.get("sid"):
            return session

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "orgUuid": ORG_UUID
    }

    # Headers "giống" trình duyệt (theo bạn cung cấp)
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://udc.vrain.vn",
        "Referer": "https://udc.vrain.vn/login",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
        "x-org-uuid": ORG_UUID,
        "x-vrain-user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
    }

    # set headers on session for subsequent requests
    session.headers.update(headers)

    app.logger.info("Attempting UDC login (POST) to %s with payload keys: %s", UDC_LOGIN_URL, list(payload.keys()))
    resp = session.post(UDC_LOGIN_URL, json=payload, timeout=15)

    app.logger.info("Login response status: %s", resp.status_code)
    app.logger.info("Login response text (truncated 1000 chars): %s", (resp.text[:1000] + '...') if len(resp.text) > 1000 else resp.text)
    app.logger.info("Response cookies: %s", resp.cookies.get_dict())
    app.logger.info("Session cookies after request: %s", session.cookies.get_dict())

    if resp.status_code != 200:
        # trả về lỗi rõ ràng để log ở Render
        raise requests.HTTPError(f"UDC login failed: {resp.status_code} - {resp.text}", response=resp)

    # kiểm tra sid cookie
    sid = session.cookies.get("sid") or resp.cookies.get("sid")
    if not sid:
        # đôi khi server trả sid trong body — show body để debug
        raise RuntimeError(f"Login OK but no 'sid' cookie found. Response body: {resp.text}")

    last_login_ts = time.time()
    app.logger.info("UDC login OK, sid present.")
    return session


@app.route("/")
def home():
    return {"status": "ok", "msg": "Flask API chạy trên Render 🎉"}


@app.route("/udc-data")
def udc_data():
    from_time = request.args.get("from")
    to_time = request.args.get("to")
    if not from_time or not to_time:
        return jsonify({"error": "Missing required params 'from' and 'to' (format YYYY-MM-DD or full datetime)"}), 400

    try:
        # ensure logged in
        if not session.cookies.get("sid"):
            login_udc()

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://udc.vrain.vn",
            "Referer": "https://udc.vrain.vn/station/detail/1h",
            "x-org-uuid": ORG_UUID,
            "x-vrain-user-agent": session.headers.get("x-vrain-user-agent", "")
        }

        payload = {
            "fromHour": "",
            "from": from_time + " 00:00:00",
            "toHour": "",
            "to": to_time + " 23:59:59",
            "i": "_10m",
            "stationGroups": []
        }

        resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)

        if resp.status_code == 401:
            app.logger.info("UDC data call returned 401 -> re-login and retry once.")
            login_udc(force=True)
            resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)

        app.logger.info("UDC data response status: %s", resp.status_code)
        app.logger.info("UDC data response cookies: %s", resp.cookies.get_dict())

        resp.raise_for_status()
        return jsonify(resp.json())

    except requests.HTTPError as e:
        app.logger.error("HTTPError while fetching UDC data: %s", e)
        code = getattr(e, "response", None).status_code if getattr(e, "response", None) else 500
        return jsonify({"error": str(e)}), code
    except Exception as e:
        app.logger.exception("Unexpected error fetching UDC data")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

