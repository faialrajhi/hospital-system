from datetime import datetime
import io
import os
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for
import pandas as pd
import requests
from supabase import Client, create_client

app = Flask(__name__)

# =========================
# Supabase Configuration
# =========================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "رابط_السوبابيس_هنا")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "مفتاح_السوبابيس_هنا")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# Meta WhatsApp Cloud API Configuration
# =========================
WHATSAPP_TOKEN = "EAAYVhdiuLegBStKMrrKepioP6n95TvkQE9JLWK3ytxWm0iJs7Bsv9smWNlQWrwZBEXWhslFpZBmzrJRJOQXRRNH74zLYajkURvbpQsJTTuU1IaOODc8nQSAU0lL2v0GZArLAnGsoqH04uifqioJtFbWcoJ8xWOPBVDWxKG8gGpZCbVUKAXj50lS9jCzWVQZDZD"
PHONE_NUMBER_ID = "1356121924253605"

# قائمة الأرقام المستلمة للإشعار
WHATSAPP_RECIPIENTS = [
    "966565142164",  # الرقم الأول
    # أضيفي باقي الأرقام الخمسة هنا بمفتاح الدولة بدون +
]


def send_whatsapp_notification(data):
    """دالة ترسل إشعار البلاغ متضمناً كافة التفاصيل بما فيها الشخص المعني والموظف المسؤول"""
    print("=== START WHATSAPP SENDING ===")
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ التوكن أو رقم الهاتف غير متاحين!")
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    # استخراج البيانات من الحقول المدخلة
    ticket_num = data.get("ticket_number", "-")
    patient_name = data.get("patient_name", "-")
    file_num = data.get("file_number", "-")
    requested_service = data.get("requested_service", "-")
    service_name = data.get("service_name", "-")
    concerned_person = data.get("concerned_person", "-")
    employee_name = data.get("employee_name", "-")

    # صياغة النص بالتنسيق الجديد متضمناً الشخص المعني والموظف المسؤول
    message_text = (
        f"رقم البلاغ/ {ticket_num}\n"
        f"اسم المستفيد / {patient_name}\n"
        f"رقم الملف/ {file_num}\n"
        f"الموضوع / {requested_service}\n"
        f"القسم / {service_name}\n"
        f"الشخص المعني / {concerned_person}\n"
        f"الموظف المسؤول / {employee_name}"
    )

    # إرسال الرسالة لكل رقم في قائمة المستلمين
    for recipient in WHATSAPP_RECIPIENTS:
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {
                "body": message_text
            }
        }

        try:
            print(f"Sending request to Meta API for recipient: {recipient}")
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"=== META API RAW RESPONSE FOR {recipient} ===")
            print("Status Code:", response.status_code)
            print("Response Body:", response.text)
        except Exception as e:
            print(f"❌ Exception caught while sending WhatsApp to {recipient}:", e)


# =========================
# Main Page
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        form_data = request.form
        ticket_number = form_data.get("ticket_number")
        patient_name = form_data.get("patient_name")
        national_id = form_data.get("national_id", "0000000000")
        file_number = form_data.get("file_number", "-")
        patient_phone = form_data.get("patient_phone", "0500000000")
        requested_service = form_data.get("requested_service")
        service_name = form_data.get("service_name")
        concerned_person = form_data.get("concerned_person", "-")
        employee_name = form_data.get("employee_name", "-")
        record_date = form_data.get("record_date")
        record_time = form_data.get("record_time")

        # حفظ بيانات البلاغ في Supabase
        record = {
            "ticket_number": ticket_number,
            "patient_name": patient_name,
            "national_id": national_id,
            "file_number": file_number,
            "patient_phone": patient_phone,
            "requested_service": requested_service,
            "service_name": service_name,
            "concerned_person": concerned_person,
            "employee_name": employee_name,
            "record_date": record_date,
            "record_time": record_time,
            "status": "new"
        }
        try:
            supabase.table("patient_records").insert(record).execute()

            # إرسال إشعار الواتساب
            send_whatsapp_notification(record)

            return redirect(url_for("index"))
        except Exception as e:
            print("Error saving record to Supabase:", e)
            return (
                jsonify({
                    "success": False,
                    "message": f"حدث خطأ أثناء حفظ البيانات: {str(e)}",
                }),
                500,
            )

    # =========================
    # جلب السجلات مرتبة بحيث يكون الأحدث في الأعلى
    # =========================
    try:
        response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
        records = response.data or []
    except Exception as e:
        print("Error fetching records from Supabase:", e)
        records = []
    return render_template("index.html", records=records)


# =========================
# Export Excel (تصدير السجلات الفعلي)
# =========================
@app.route("/export-excel", methods=["GET"])
def export_excel():
    try:
        response = supabase.table("patient_records").select("*").execute()
        records = response.data or []

        if not records:
            return jsonify({"success": False, "message": "لا توجد سجلات لتصديرها."}), 404

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
                "الموظف المسؤول": r.get("employee_name", "-"),
                "التاريخ": r.get("record_date", "-"),
                "الوقت": r.get("record_time", "-"),
                "الإجراء المتخذ والملاحظات": r.get("action_notes", "-")
            })

        df = pd.DataFrame(formatted_data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='بلاغات 937')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='hospital_records_937.xlsx'
        )
    except Exception as e:
        print("Error exporting to Excel:", e)
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# حفظ ملاحظات الإجراء وتغيير الحالة
# =========================
@app.route("/save-note", methods=["POST"])
def save_note():
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        action_notes = data.get("action_notes", "").strip()
        status = data.get("status", "new")

        if not record_id:
            return (
                jsonify(
                    {"success": False, "message": "لم يتم تحديد سجل البلاغ."}
                ),
                400,
            )

        response = (
            supabase.table("patient_records")
            .update({
                "action_notes": action_notes,
                "status": status
            })
            .eq("id", record_id)
            .execute()
        )
        return jsonify(
            {"success": True, "message": "تم تحديث حالة البلاغ والملاحظات بنجاح."}
        )
    except Exception as e:
        print("Error saving patient note:", e)
        return (
            jsonify({
                "success": False,
                "message": f"حدث خطأ أثناء حفظ البيانات: {str(e)}",
            }),
            500,
        )


# =========================
# Run App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
