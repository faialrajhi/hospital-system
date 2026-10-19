from datetime import datetime
import io
import os
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for, session
import pandas as pd
import requests
from supabase import Client, create_client

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "hospital_937_secret_key_2026")

# =========================
# قائمة الموظفين (اسم المستخدم، كلمة المرور، والاسم العربي الكامل)
# =========================
USERS = {
    "abdullah": {"password": "123", "name": "عبدالله الزهراني"},
    "ahmed": {"password": "123", "name": "احمد عيسى"},
    "ebtisam": {"password": "123", "name": "ابتسام المغامسي"},
    "nozha": {"password": "123", "name": "نزهه السلولي"},
    "khaled": {"password": "123", "name": "خالد الزهراني"}
}

# =========================
# Supabase Configuration
# =========================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://urnawuapfkhxvqvepzit.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVybmF3dWFwZmtoeHZxdmVweml0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODA5NTQxMCwiZXhwIjoyMTAzNjcxNDEwfQ.hg8Ki6qvoI_Fhammt_87t-HfTZPSdvl6nYn5bUtThzo")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# Green API Configuration
# =========================
GREEN_API_INSTANCE_ID = os.environ.get("GREEN_API_INSTANCE_ID", "710722772629")
GREEN_API_TOKEN = os.environ.get("GREEN_API_TOKEN2", os.environ.get("GREEN_API_TOKEN", "e2ff31ea0b24f838a230552e4acabd61fd93c37be6d408ebd"))
WHATSAPP_GROUP_ID = os.environ.get("WHATSAPP_GROUP_ID", "120363044377285466@g.us")


def get_next_ticket_number():
    """يحسب رقم البلاغ التالي بدقة بناءً على عدد السجلات الفعلية + 1"""
    try:
        response = supabase.table("patient_records").select("id", count="exact").execute()
        total_records = len(response.data) if response.data else 0
        next_id = total_records + 1
        return f"B{next_id}"
    except Exception as e:
        print("Error calculating next ticket number:", e)
        return "B1"


def send_whatsapp_notification(data):
    """دالة ترسل إشعار البلاغ آلياً لمجموعة الواتساب عبر Green API مع اسم الموظف العربي"""
    if not GREEN_API_TOKEN:
        return

    url = f"https://7107.api.greenapi.com/waInstance{GREEN_API_INSTANCE_ID}/sendMessage/{GREEN_API_TOKEN}"

    message_text = (
        f"رقم البلاغ/ {data.get('ticket_number', '-')}\n"
        f"اسم المستفيد / {data.get('patient_name', '-')}\n"
        f"رقم الملف/ {data.get('file_number', '-')}\n"
        f"الموضوع / {data.get('requested_service', '-')}\n"
        f"القسم / {data.get('service_name', '-')}\n"
        f"الشخص المعني / {data.get('concerned_person', '-')}\n"
        f"موظف تجربة المريض / {data.get('employee_name', '-')}"
    )

    payload = {"chatId": WHATSAPP_GROUP_ID, "message": message_text}
    headers = {"Content-Type": "application/json"}

    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        print("❌ Error sending WhatsApp message:", e)


# =========================
# مسار تسجيل الدخول Login
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()

        if username in USERS and USERS[username]["password"] == password:
            session["user"] = username
            session["employee_name"] = USERS[username]["name"] # حفظ الاسم العربي الكامل في الجلسة
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="اسم المستخدم أو كلمة المرور غير صحيحة")

    return render_template("login.html")


# =========================
# تسجيل الخروج Logout
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# الصفحة الرئيسية (محمية بتسجيل الدخول)
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        form_data = request.form
        ticket_number = get_next_ticket_number()

        # أخذ اسم الموظف تلقائياً من الـ session (الاسم العربي الكامل)
        logged_emp_name = session.get("employee_name", "موظف النظام")

        record = {
            "ticket_number": ticket_number,
            "patient_name": form_data.get("patient_name"),
            "national_id": form_data.get("national_id", "0000000000"),
            "file_number": form_data.get("file_number", "-"),
            "patient_phone": form_data.get("patient_phone", "0500000000"),
            "requested_service": form_data.get("requested_service"),
            "service_name": form_data.get("service_name"),
            "concerned_person": form_data.get("concerned_person", "-"),
            "employee_name": logged_emp_name,
            "record_date": form_data.get("record_date"),
            "record_time": form_data.get("record_time"),
            "status": "new"
        }
        try:
            supabase.table("patient_records").insert(record).execute()
            send_whatsapp_notification(record)
            return redirect(url_for("index"))
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    try:
        response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
        records = response.data or []
    except Exception as e:
        records = []

    next_ticket_number = get_next_ticket_number()

    return render_template("index.html", records=records, next_ticket_number=next_ticket_number, logged_employee=session.get("employee_name"))


# =========================
# تصدير ملف Excel
# =========================
@app.route("/export-excel", methods=["GET"])
def export_excel():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
        records = response.data or []

        if not records:
            return jsonify({"success": False, "message": "لا توجد سجلات."}), 404

        formatted_data = []
        for r in records:
            formatted_data.append({
                "حالة البلاغ": r.get("status", "-"),
                "رقم البلاغ": r.get("ticket_number", "-"),
                "رقم الملف": r.get("file_number", "-"),
                "اسم المبلغ": r.get("patient_name", "-"),
                "الموضوع": r.get("requested_service", "-"),
                "القسم المعني": r.get("service_name", "-"),
                "الشخص المعني": r.get("concerned_person", "-"),
                "موظف تجربة المريض": r.get("employee_name", "-"),
                "التاريخ": r.get("record_date", "-"),
                "الوقت": r.get("record_time", "-")
            })

        df = pd.DataFrame(formatted_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='بلاغات 937')
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name='hospital_records_937.xlsx')
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/save-note", methods=["POST"])
def save_note():
    if "user" not in session:
        return jsonify({"success": False, "message": "غير مصرح."}), 401
    try:
        data = request.get_json()
        supabase.table("patient_records").update({"status": data.get("status")}).eq("id", data.get("record_id")).execute()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
