# proxy.py
from flask import Flask, request, jsonify
import requests
import time
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# ---------- CẤU HÌNH ----------
UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
UDC_API_DETAILS = "https://udc.vrain.vn/api/private/v1/organizations/details"

USERNAME = "udchcm"   # thay bằng tài khoản thật
PASSWORD = "123456"   # thay bằng mật khẩu thật
ORG_UUID = "b147bbcd-0371-4cab-9052-151660e86ea5"

# session toàn cục
session = requests.Session()
last_login_ts = 0
# --------------------------------


def login_udc(force=False):
    """Đăng nhập UDC và lưu cookie sid"""
    global last_login_ts, session

    if not force and time.time() - last_login_ts < 600:
        if session.cookies.get("sid"):
            return session

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "orgUuid": ORG_UUID
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://udc.vrain.vn",
        "Referer": "https://udc.vrain.vn/login",
        "User-Agent": "Mozilla/5.0",
        "x-org-uuid": ORG_UUID,
        "x-vrain-user-agent": "Mozilla/5.0"
    }

    session.headers.update(headers)
    resp = session.post(UDC_LOGIN_URL, json=payload, timeout=15)

    if resp.status_code != 200:
        raise requests.HTTPError(f"UDC login failed: {resp.status_code} - {resp.text}", response=resp)

    sid = session.cookies.get("sid") or resp.cookies.get("sid")
    if not sid:
        raise RuntimeError(f"Login OK but no 'sid' cookie found. Body: {resp.text}")

    last_login_ts = time.time()
    app.logger.info("UDC login OK, sid=%s", sid)
    return session


@app.route("/")
def home():
    return {"status": "ok", "msg": "Flask API chạy trên Render 🎉"}


@app.route("/udc-data")
def udc_data():
    try:
        # Ưu tiên dùng param ?date=YYYY-MM-DD hoặc dd/MM/yyyy
        date_str = request.args.get("date")

        if date_str:
            try:
                day = datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                day = datetime.strptime(date_str, "%Y-%m-%d")

            start_date = day
            end_date = start_date + timedelta(days=1)
            # day = datetime.strptime("2025-09-21", "%Y-%m-%d")
            T_START = datetime(day.year, day.month, day.day, 0, 0, 0)
            T_END   = T_START + timedelta(days=1)


            from_time = start_date.strftime("%Y-%m-%d")
            to_time = end_date.strftime("%Y-%m-%d")
        

        else:
            # fallback nếu dùng ?from=YYYY-MM-DD&to=YYYY-MM-DD
            from_time = request.args.get("from")
            to_time = request.args.get("to")
            if not from_time or not to_time:
                return jsonify({"error": "Missing param 'date' hoặc 'from' + 'to'"}), 400

        # đảm bảo login
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
            "from": from_time,
            "toHour": "",
            "to": to_time,
            "i": "_10m",
            "stationGroups": []
        }

        resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)
        if resp.status_code == 401:
            app.logger.warning("401 Unauthorized -> re-login and retry")
            login_udc(force=True)
            resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)

        resp.raise_for_status()
        data = resp.json()        
        result = {}
        for entry in data.get("stats", []):
            time_point = entry.get("timePoint")
            try:
                if " " in time_point and "/" in time_point:
                    hhmm, dmy = time_point.split()
                    dt = datetime.strptime(f"{dmy} {hhmm}", "%d/%m %H:%M")
                    dt = dt.replace(year=day.year)
                else:
                    dt = datetime.strptime(time_point, "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue

            if not (T_START <= dt < T_END):
                continue
       
            for station in entry.get("stations", []):
                name = station.get("name", "Unknown")
                hhmm = dt.strftime("%H:%M")
                depth = station.get("depth", 0.0)

                if depth == "-" or depth is None:
                    depth = 0.0
                else:
                    try:
                        depth = float(depth)
                    except:
                        depth = 0.0
               
                 # 👉 Lưu dưới dạng chuỗi y chang bạn muốn
                line = f"{hhmm}  {depth}"        
                result.setdefault(name, [])
                result[name].append(line)
        return jsonify(result)

    except Exception as e:
        app.logger.exception("Unexpected error fetching UDC data")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# -----------------------------------------------------------


























































