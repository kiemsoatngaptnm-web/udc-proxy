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
        # result = {}

        # if "stats" not in data:
        #     app.logger.warning("Không tìm thấy key 'stats' trong JSON: %s", list(data.keys()))
        #     return jsonify({"error": "UDC JSON format unexpected", "keys": list(data.keys())}), 500

        # for entry in data["stats"]:
        #     time_point = entry.get("timePoint")
        #     for station in entry.get("stations", []):
        #         name = station.get("name", "Unknown")
        #         depth = station.get("depth", "NA")
        #         # Format: "HH:MM  value"
        #         try:
        #             if " " in time_point:  # ví dụ "19:10 21/09"
        #                 hhmm = time_point.split()[0]
        #             else:
        #                 hhmm = time_point[11:16]
        #         except Exception:
        #             hhmm = str(time_point)

        #         formatted = f"{hhmm}  {depth}"
        #         result.setdefault(name, []).append(formatted)
        # result = {}
        # for entry in data.get("stats", []):
        #     time_point = entry.get("timePoint")
        #     # chuyển timePoint -> datetime
        #     dt = None
        #     try:
        #         # nếu kiểu "19:10 23/09"
        #         if " " in time_point and "/" in time_point:
        #             hhmm, dmy = time_point.split()
        #             dt = datetime.strptime(f"{dmy} {hhmm}", "%d/%m %H:%M")
        #             dt = dt.replace(year=day.year)  # bổ sung năm
        #         else:
        #             dt = datetime.strptime(time_point, "%Y-%m-%d %H:%M:%S")
        #     except Exception:
        #         continue
        
        #     # lọc theo khoảng ngày
        #     if not (T_START <= dt < T_END):
        #         continue
        
        #     for station in entry.get("stations", []):
        #         name = station.get("name", "Unknown")
        #         depth = station.get("depth", "NA")
        #         hhmm = dt.strftime("%H:%M")
        #         formatted = f"{hhmm} {depth}"
        #         result.setdefault(name, []).append(formatted)


        # return jsonify(result)
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
                    depth = station.get("depth", 0)
                    hhmm = dt.strftime("%H:%M")
    
                    if name not in result:
                        result[name] = f"({name} "
                    result[name] += f"{hhmm} {depth} "
    
            # đóng ngoặc cho từng chuỗi
            for name in result:
                result[name] = result[name].strip() + ")"

            return jsonify(result)

    except Exception as e:
        app.logger.exception("Unexpected error fetching UDC data")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

# --------------------------------
# # proxy.py
# from flask import Flask, request, jsonify
# import requests
# import time
# import logging

# app = Flask(__name__)
# app.logger.setLevel(logging.INFO)

# # ---------- CẤU HÌNH ----------
# UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
# UDC_API_DETAILS = "https://udc.vrain.vn/api/private/v1/organizations/details"

# USERNAME = "udchcm"   # thay bằng tài khoản thật
# PASSWORD = "123456"   # thay bằng mật khẩu thật
# ORG_UUID = "b147bbcd-0371-4cab-9052-151660e86ea5"

# # session toàn cục
# session = requests.Session()
# last_login_ts = 0
# # --------------------------------


# def login_udc(force=False):
#     """Đăng nhập UDC và lưu cookie sid"""
#     global last_login_ts, session

#     if not force and time.time() - last_login_ts < 600:
#         if session.cookies.get("sid"):
#             return session

#     payload = {
#         "username": USERNAME,
#         "password": PASSWORD,
#         "orgUuid": ORG_UUID
#     }

#     headers = {
#         "Accept": "application/json, text/plain, */*",
#         "Content-Type": "application/json",
#         "Origin": "https://udc.vrain.vn",
#         "Referer": "https://udc.vrain.vn/login",
#         "User-Agent": "Mozilla/5.0",
#         "x-org-uuid": ORG_UUID,
#         "x-vrain-user-agent": "Mozilla/5.0"
#     }

#     session.headers.update(headers)
#     resp = session.post(UDC_LOGIN_URL, json=payload, timeout=15)

#     if resp.status_code != 200:
#         raise requests.HTTPError(f"UDC login failed: {resp.status_code} - {resp.text}", response=resp)

#     sid = session.cookies.get("sid") or resp.cookies.get("sid")
#     if not sid:
#         raise RuntimeError(f"Login OK but no 'sid' cookie found. Body: {resp.text}")

#     last_login_ts = time.time()
#     app.logger.info("UDC login OK, sid=%s", sid)
#     return session


# @app.route("/")
# def home():
#     return {"status": "ok", "msg": "Flask API chạy trên Render 🎉"}


# @app.route("/udc-data")
# def udc_data():
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     if not from_time or not to_time:
#         return jsonify({"error": "Missing params 'from' and 'to' (YYYY-MM-DD or full datetime)"}), 400

#     try:
#         if not session.cookies.get("sid"):
#             login_udc()

#         headers = {
#             "Content-Type": "application/json",
#             "Origin": "https://udc.vrain.vn",
#             "Referer": "https://udc.vrain.vn/station/detail/1h",
#             "x-org-uuid": ORG_UUID,
#             "x-vrain-user-agent": session.headers.get("x-vrain-user-agent", "")
#         }

#         payload = {
#             "fromHour": "",
#             "from": from_time,
#             "toHour": "",
#             "to": to_time,
#             "i": "_10m",
#             "stationGroups": []
#         }

#         resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)
#         if resp.status_code == 401:
#             app.logger.warning("401 Unauthorized -> re-login and retry")
#             login_udc(force=True)
#             resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)


#         resp.raise_for_status()
#         # return jsonify(resp.json())
#         data = resp.json()
#         result = {}
        
#         if "stats" not in data:
#             app.logger.warning("Không tìm thấy key 'stats' trong JSON: %s", list(data.keys()))
#             return jsonify({"error": "UDC JSON format unexpected", "keys": list(data.keys())}), 500
        
#         for entry in data["stats"]:
#             time_point = entry.get("timePoint")
#             for station in entry.get("stations", []):
#                 name = station.get("name", "Unknown")
#                 depth = station.get("depth", "NA")
#                 # Format: "HH:MM  value"
#                 try:
#                     if " " in time_point:  # ví dụ "19:10 21/09"
#                         hhmm = time_point.split()[0]  # lấy "19:10"
#                     else:
#                         hhmm = time_point[11:16]  # fallback cho dạng ISO
#                 except Exception:
#                     hhmm = str(time_point)
        
#                 formatted = f"{hhmm}  {depth}"
#                 result.setdefault(name, []).append(formatted)
        
#         return jsonify(result)

#         # resp.raise_for_status()
#         # data = resp.json()

#         # # --------- CHUYỂN ĐỔI DỮ LIỆU ---------
#         # result = {}
#         # # kiểm tra xem JSON có gì
#         # if "stations" in data:  # kiểu 1: data trực tiếp
#         #     stations = data["stations"]
#         # elif "data" in data and "stations" in data["data"]:  # kiểu 2: nằm trong data
#         #     stations = data["data"]["stations"]
#         # else:
#         #     app.logger.warning("Không tìm thấy key 'stations' trong JSON: %s", list(data.keys()))
#         #     return jsonify({"error": "Không tìm thấy dữ liệu 'stations'", "raw": data}), 500

#         # for st in stations:
#         #     # tên trạm: có thể là "name" hoặc "stationName"
#         #     name = st.get("name") or st.get("stationName") or "Unknown"

#         #     values = []
#         #     # dữ liệu có thể là "data" hoặc "stats"
#         #     for item in st.get("data", []) + st.get("stats", []):
#         #         t = item.get("time") or item.get("timePoint")
#         #         v = item.get("value") or item.get("depth")
#         #         if not t or v is None:
#         #             continue
#         #         hhmm = t[11:16] if len(t) >= 16 else t
#         #         values.append(f"{hhmm}  {v}")

#         #     result[name] = values

#         # return jsonify(result)

#         # data = resp.json()
#         # result = {}
        
#         # # kiểm tra có key stats không
#         # if "stats" not in data:
#         #     app.logger.warning("Không tìm thấy key 'stats' trong JSON: %s", list(data.keys()))
#         #     return jsonify({"error": "UDC JSON format unexpected", "keys": list(data.keys())}), 500
        
#         # for station in data["stats"]:
#         #     name = station.get("stationName", "Unknown")
#         #     values = []
#         #     for item in station.get("data", []):
#         #         t = item.get("timePoint") or item.get("time")
#         #         v = item.get("depth") or item.get("value")
#         #         # format "HH:MM  value"
#         #         try:
#         #             hhmm = t[11:16]  # lấy giờ:phút từ "YYYY-MM-DD HH:MM:SS"
#         #         except Exception:
#         #             hhmm = str(t)
#         #         values.append(f"{hhmm}  {v}")
#         #     result[name] = values
        
#         # return jsonify(result)

    
#     except Exception as e:
#         app.logger.exception("Unexpected error fetching UDC data")
#         return jsonify({"error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

# -------------------------------------------------------------
# # proxy.py
# from flask import Flask, request, jsonify
# import requests
# import time
# import logging

# app = Flask(__name__)
# app.logger.setLevel(logging.INFO)

# # ---------- CẤU HÌNH ----------
# UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
# UDC_API_DETAILS = "https://udc.vrain.vn/api/private/v1/organizations/details"

# USERNAME = "udchcm"   # thay bằng tài khoản thật
# PASSWORD = "123456"   # thay bằng mật khẩu thật
# ORG_UUID = "b147bbcd-0371-4cab-9052-151660e86ea5"

# # session toàn cục
# session = requests.Session()
# last_login_ts = 0
# # --------------------------------


# def login_udc(force=False):
#     """Đăng nhập UDC và lưu cookie sid"""
#     global last_login_ts, session

#     if not force and time.time() - last_login_ts < 600:
#         if session.cookies.get("sid"):
#             return session

#     payload = {
#         "username": USERNAME,
#         "password": PASSWORD,
#         "orgUuid": ORG_UUID
#     }

#     headers = {
#         "Accept": "application/json, text/plain, */*",
#         "Content-Type": "application/json",
#         "Origin": "https://udc.vrain.vn",
#         "Referer": "https://udc.vrain.vn/login",
#         "User-Agent": "Mozilla/5.0",
#         "x-org-uuid": ORG_UUID,
#         "x-vrain-user-agent": "Mozilla/5.0"
#     }

#     session.headers.update(headers)
#     resp = session.post(UDC_LOGIN_URL, json=payload, timeout=15)

#     if resp.status_code != 200:
#         raise requests.HTTPError(f"UDC login failed: {resp.status_code} - {resp.text}", response=resp)

#     sid = session.cookies.get("sid") or resp.cookies.get("sid")
#     if not sid:
#         raise RuntimeError(f"Login OK but no 'sid' cookie found. Body: {resp.text}")

#     last_login_ts = time.time()
#     app.logger.info("UDC login OK, sid=%s", sid)
#     return session


# @app.route("/")
# def home():
#     return {"status": "ok", "msg": "Flask API chạy trên Render 🎉"}


# @app.route("/udc-data")
# def udc_data():
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     if not from_time or not to_time:
#         return jsonify({"error": "Missing params 'from' and 'to' (YYYY-MM-DD or full datetime)"}), 400

#     try:
#         if not session.cookies.get("sid"):
#             login_udc()

#         headers = {
#             "Content-Type": "application/json",
#             "Origin": "https://udc.vrain.vn",
#             "Referer": "https://udc.vrain.vn/station/detail/1h",
#             "x-org-uuid": ORG_UUID,
#             "x-vrain-user-agent": session.headers.get("x-vrain-user-agent", "")
#         }

#         payload = {
#             "fromHour": "",
#             "from": from_time,
#             "toHour": "",
#             "to": to_time,
#             "i": "_10m",
#             "stationGroups": []
#         }

#         resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)
#         if resp.status_code == 401:
#             app.logger.warning("401 Unauthorized -> re-login and retry")
#             login_udc(force=True)
#             resp = session.post(UDC_API_DETAILS, headers=headers, json=payload, timeout=30)


#         resp.raise_for_status()
#         return jsonify(resp.json())
#         # resp.raise_for_status()
#         # data = resp.json()

#         # # --------- CHUYỂN ĐỔI DỮ LIỆU ---------
#         # result = {}
#         # # kiểm tra xem JSON có gì
#         # if "stations" in data:  # kiểu 1: data trực tiếp
#         #     stations = data["stations"]
#         # elif "data" in data and "stations" in data["data"]:  # kiểu 2: nằm trong data
#         #     stations = data["data"]["stations"]
#         # else:
#         #     app.logger.warning("Không tìm thấy key 'stations' trong JSON: %s", list(data.keys()))
#         #     return jsonify({"error": "Không tìm thấy dữ liệu 'stations'", "raw": data}), 500

#         # for st in stations:
#         #     # tên trạm: có thể là "name" hoặc "stationName"
#         #     name = st.get("name") or st.get("stationName") or "Unknown"

#         #     values = []
#         #     # dữ liệu có thể là "data" hoặc "stats"
#         #     for item in st.get("data", []) + st.get("stats", []):
#         #         t = item.get("time") or item.get("timePoint")
#         #         v = item.get("value") or item.get("depth")
#         #         if not t or v is None:
#         #             continue
#         #         hhmm = t[11:16] if len(t) >= 16 else t
#         #         values.append(f"{hhmm}  {v}")

#         #     result[name] = values

#         # return jsonify(result)

#         # data = resp.json()
#         # result = {}
        
#         # # kiểm tra có key stats không
#         # if "stats" not in data:
#         #     app.logger.warning("Không tìm thấy key 'stats' trong JSON: %s", list(data.keys()))
#         #     return jsonify({"error": "UDC JSON format unexpected", "keys": list(data.keys())}), 500
        
#         # for station in data["stats"]:
#         #     name = station.get("stationName", "Unknown")
#         #     values = []
#         #     for item in station.get("data", []):
#         #         t = item.get("timePoint") or item.get("time")
#         #         v = item.get("depth") or item.get("value")
#         #         # format "HH:MM  value"
#         #         try:
#         #             hhmm = t[11:16]  # lấy giờ:phút từ "YYYY-MM-DD HH:MM:SS"
#         #         except Exception:
#         #             hhmm = str(t)
#         #         values.append(f"{hhmm}  {v}")
#         #     result[name] = values
        
#         # return jsonify(result)

    
#     except Exception as e:
#         app.logger.exception("Unexpected error fetching UDC data")
#         return jsonify({"error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)

# -----------------------------------------------------------------------

# # proxy.py
# from flask import Flask, request, jsonify
# import requests
# import time
# import logging

# app = Flask(__name__)
# app.logger.setLevel(logging.INFO)

# # ---------- CẤU HÌNH ----------
# UDC_LOGIN_URL = "https://udc.vrain.vn/api/public/v2/login"
# UDC_API_DETAILS = "https://udc.vrain.vn/api/private/v1/organizations/details"

# # Thay bằng tài khoản thực tế
# USERNAME = "udchcm"
# PASSWORD = "123456"
# ORG_UUID = "b147bbcd-0371-4cab-9052-151660e86ea5"

# # Session toàn cục để giữ cookie sid
# session = requests.Session()
# last_login_ts = 0
# # --------------------------------

# def login_udc(force=False):
#     global last_login_ts, session

#     # tránh login quá thường (10 phút)
#     if not force and time.time() - last_login_ts < 600:
#         if session.cookies.get("sid"):
#             return session

#     payload = {
#         "username": USERNAME,
#         "password": PASSWORD,
#         "orgUuid": ORG_UUID
#     }

#     # Headers "giống" trình duyệt (theo bạn cung cấp)
#     headers = {
#         "Accept": "application/json, text/plain, */*",
#         "Accept-Language": "en-US,en;q=0.9",
#         "Content-Type": "application/json",
#         "Origin": "https://udc.vrain.vn",
#         "Referer": "https://udc.vrain.vn/login",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
#         "x-org-uuid": ORG_UUID,
#         "x-vrain-user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
#     }

#     # set headers on session for subsequent requests
#     session.headers.update(headers)

#     app.logger.info("Attempting UDC login (POST) to %s with payload keys: %s", UDC_LOGIN_URL, list(payload.keys()))
#     resp = session.post(UDC_LOGIN_URL, json=payload, timeout=15)

#     app.logger.info("Login response status: %s", resp.status_code)
#     app.logger.info("Login response text (truncated 1000 chars): %s", (resp.text[:1000] + '...') if len(resp.text) > 1000 else resp.text)
#     app.logger.info("Response cookies: %s", resp.cookies.get_dict())
#     app.logger.info("Session cookies after request: %s", session.cookies.get_dict())

#     if resp.status_code != 200:
#         # trả về lỗi rõ ràng để log ở Render
#         raise requests.HTTPError(f"UDC login failed: {resp.status_code} - {resp.text}", response=resp)

#     # kiểm tra sid cookie
#     sid = session.cookies.get("sid") or resp.cookies.get("sid")
#     if not sid:
#         # đôi khi server trả sid trong body — show body để debug
#         raise RuntimeError(f"Login OK but no 'sid' cookie found. Response body: {resp.text}")

#     last_login_ts = time.time()
#     app.logger.info("UDC login OK, sid present.")
#     return session


# @app.route("/")
# def home():
#     return {"status": "ok", "msg": "Flask API chạy trên Render 🎉"}


# @app.route("/udc-data")
# def udc_data():
#     from_time = request.args.get("from")
#     to_time = request.args.get("to")
#     if not from_time or not to_time:
#         return jsonify({"error": "Missing required params 'from' and 'to' (format YYYY-MM-DD or full datetime)"}), 400   
#     # if not from_time or not to_time:
#     #     return jsonify({"error": "Missing params 'from' and 'to'"}), 400

#     # # Nếu người dùng chỉ nhập ngày -> thêm giờ mặc định
#     # if len(from_time) == 10:  # dạng YYYY-MM-DD
#     #     from_time = from_time + " 00:00:00"
#     # if len(to_time) == 10:
#     #     to_time = to_time + " 23:59:59"
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
#         #     "from": from_time + " 00:00:00",
#         #     "toHour": "",
#         #     "to": to_time + " 23:59:59",
#         #     "i": "_10m",
#         #     "stationGroups": []
#         # }

#         # payload = {
#         #     "fromHour": None,
#         #     "from": from_time,
#         #     "toHour": None,
#         #     "to": to_time,
#         #     "i": "_10m",
#         #     "stationGroups": []
#         # }
        

#         payload = {
#             "fromHour": "",
#             "from": from_time,   # giờ–phút–giây do client truyền hoặc auto bổ sung
#             "toHour": "",
#             "to": to_time,
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
#         # resp.raise_for_status()
#         # data = resp.json()
#         # app.logger.info("UDC raw JSON top-level keys: %s", list(data.keys()))
#         # result = {}
        
#         # Ví dụ response có dạng:
#         # {
#         #   "stations": [
#         #       {
#         #           "name": "Nguyễn Thiện Thuật",
#         #           "data": [
#         #               {"time": "2025-09-22 16:45:00", "value": 0.0},
#         #               {"time": "2025-09-22 17:00:00", "value": 0.0}
#         #           ]
#         #       },
#         #       ...
#         #   ]
#         # }
        
#         # for station in data.get("stations", []):
#         #     name = station.get("name", "Unknown")
#         #     values = []
#         #     for item in station.get("data", []):
#         #         t = item.get("time")
#         #         v = item.get("value")
#         #         # format "HH:MM  value"
#         #         try:
#         #             hhmm = t[11:16]  # lấy giờ:phút từ "YYYY-MM-DD HH:MM:SS"
#         #         except:
#         #             hhmm = t
#         #         values.append(f"{hhmm}  {v}")
#         #     result[name] = values
        
#         # return jsonify(result)


#     except requests.HTTPError as e:
#         app.logger.error("HTTPError while fetching UDC data: %s", e)
#         code = getattr(e, "response", None).status_code if getattr(e, "response", None) else 500
#         return jsonify({"error": str(e)}), code
#     except Exception as e:
#         app.logger.exception("Unexpected error fetching UDC data")
#         return jsonify({"error": str(e)}), 500



# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)










































