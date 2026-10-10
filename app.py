from datetime import datetime
import os
from flask import Flask, jsonify, redirect, render_template, request, url_for
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
WHATSAPP_RECIPIENT = "966565142164"  # رقم الجوال المستلم لتجربة الإرسال


def send_whatsapp_notification(data):
    """دالة ترسل إشعار البلاغ متضمناً تفاصيل المريض والبلاغ عبر واتساب ميتا"""
    print("=== START WHATSAPP SENDING ===")
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("⚠️ التوكن أو رقم الهاتف غير متاحين!")
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    # تجهيز نص رسالة البلاغ ليرسل كبيانات واضحة
    ticket_num = data.get("ticket_number", "غير محدد")
    patient_name = data.get("patient_name", "غير محدد")
    service_name = data.get("requested_service") or data.get("service_name", "غير محدد")
    employee = data.get("employee_name", "غير محدد")
    rec_date = data.get("record_date", "")
    rec_time = data.get("record_time", "")

    # استخدام رسالة تفصيلية (في حال فتح نافذة المحادثة أو استخدام القالب)
    # ملاحظة: في حال استخدام قالب مخصص لاحقاً يتم تمريرها في الـ components
    message_text = (
        f"🚨 *إشعار بلاغ طبي جديد*\n\n"
        f"📌 *رقم البلاغ:* {ticket_num}\n"
        f"👤 *اسم المريض:* {patient_name}\n"
        f"🛠 *الخدمة المطلوبة:* {service_name}\n"
        f"👨‍💻 *الموظف المسؤول:* {employee}\n"
        f"📅 *الوقت:* {rec_date} {rec_time}"
    )

    # نظراً لأن الرقم التجريبي يتطلب قوالب للنصوص الحرة غير المسجلة، 
    # سنقوم بإرسال النص كرسالة نصية مباشرة (تتطلب تفاعل سابق بـ hi من المستلم لتفتح نافذة 24 ساعة):
    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_RECIPIENT,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    try:
        print(f"Sending request to Meta API for recipient: {WHATSAPP_RECIPIENT}")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print("=== META API RAW RESPONSE ===")
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
    except Exception as e:
        print("❌ Exception caught while sending WhatsApp:", e)


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
        employee_name = form_data.get("employee_name")
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
            "employee_name": employee_name,
            "record_date": record_date,
            "record_time": record_time,
        }
        try:
            supabase.table("patient_records").insert(record).execute()

            # إرسال إشعار الواتساب تفصيلياً من السيرفر بعد نجاح الحفظ
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
    # جلب السجلات
    # =========================
    try:
        response = supabase.table("patient_records").select("*").execute()
        records = response.data or []
    except Exception as e:
        print("Error fetching records from Supabase:", e)
        records = []
    return render_template("index.html", records=records)


# =========================
# Export Excel
# =========================
@app.route("/export-excel", methods=["GET"])
def export_excel():
    return jsonify({
        "success": True,
        "message": "تم طلب تصدير السجلات إلى إكسل بنجاح.",
    })


# =========================
# حفظ ملاحظات الإجراء
# =========================
@app.route("/save-note", methods=["POST"])
def save_note():
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        action_notes = data.get("action_notes", "").strip()

        if not record_id:
            return (
                jsonify(
                    {"success": False, "message": "لم يتم تحديد سجل البلاغ."}
                ),
                400,
            )

        if not action_notes:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "يرجى كتابة تفاصيل الإجراء المتخذ.",
                    }
                ),
                400,
            )

        response = (
            supabase.table("patient_records")
            .update({"action_notes": action_notes})
            .eq("id", record_id)
            .execute()
        )
        return jsonify(
            {"success": True, "message": "تم حفظ تفاصيل الإجراء المتخذ بنجاح."}
        )
    except Exception as e:
        print("Error saving patient note:", e)
        return (
            jsonify({
                "success": False,
                "message": f"حدث خطأ أثناء حفظ الملاحظة: {str(e)}",
            }),
            500,
        )


# =========================
# Run App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
