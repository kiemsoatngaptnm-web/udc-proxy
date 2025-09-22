
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

        # payload = {
        #     "fromHour": "",
        #     "from": from_time + " 00:00:00",
        #     "toHour": "",
        #     "to": to_time + " 23:59:59",
        #     "i": "_10m",
        #     "stationGroups": []
        # }

        payload = {
            "fromHour": None,
            "from": from_time,
            "toHour": None,
            "to": to_time,
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

# @app.route("/udc-data")
# def udc_data():
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     if not from_time or not to_time:
#         return jsonify({"error": "Missing required params 'from' and 'to' (format YYYY-MM-DD or full datetime)"}), 400

#     # Nếu chỉ có YYYY-MM-DD thì thêm giờ mặc định
#     if len(from_time) == 10:  # dạng "YYYY-MM-DD"
#         from_time = from_time + " 00:00:00"
#     if len(to_time) == 10:
#         to_time = to_time + " 23:59:59"

#     try:
#         # ensure logged in
#         if not session.cookies.get("sid"):
#             login_udc()

#         headers = {
#             "Content-Type": "application/json",
#             "Origin": "https://udc.vrain.vn",
#             "Referer": "https://udc.vrain.vn/station/detail/1h",
#             "x-org-uuid": ORG_UUID,
#             "x-vrain-user-agent": session.headers.get("x-vrain-user-agent", "")
#         }

#         # payload = {
#         #     "fromHour": "",
#         #     "from": from_time,
#         #     "toHour": "",
#         #     "to": to_time,
#         #     "i": "_10m",
#         #     "stationGroups": []
#         # }
#         payload = {
#             "fromHour": "",
#             "from": from_time + " 00:00:00",
#             "toHour": "",
#             "to": to_time + " 23:59:59",
#             "i": "_10m",
#             "stationGroups": []
#         }
#         resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)

#         if resp.status_code == 401:
#             app.logger.info("UDC data call returned 401 -> re-login and retry once.")
#             login_udc(force=True)
#             resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)

#         app.logger.info("UDC data response status: %s", resp.status_code)
#         app.logger.info("UDC data response cookies: %s", resp.cookies.get_dict())

#         resp.raise_for_status()
#         return jsonify(resp.json())

#     except requests.HTTPError as e:
#         app.logger.error("HTTPError while fetching UDC data: %s", e)
#         code = getattr(e, "response", None).status_code if getattr(e, "response", None) else 500
#         return jsonify({"error": str(e)}), code
#     except Exception as e:
#         app.logger.exception("Unexpected error fetching UDC data")
#         return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)








