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
WHATSAPP_TOKEN = "4551928168459746"
PHONE_NUMBER_ID = "1356121924253605"
WHATSAPP_RECIPIENT = "966565142164"  # رقم الجوال المستلم لتجربة الإرسال


def send_whatsapp_notification(data):
  """دالة ترسل إشعار البلاغ إلى واتساب عبر API ميتا في الخلفية تلقائياً"""
  if (
      not WHATSAPP_TOKEN
      or "ضع_التوكن" in WHATSAPP_TOKEN
      or not PHONE_NUMBER_ID
      or "ضع_معرف" in PHONE_NUMBER_ID
  ):
    print(
        "⚠️ تنبيه: لم يتم ضبط بيانات Meta WhatsApp API بعد. تم تخطي إرسال الواتساب"
        " مؤقتاً."
    )
    return

  url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
  headers = {
      "Authorization": f"Bearer {WHATSAPP_TOKEN}",
      "Content-Type": "application/json",
  }

  message_text = (
      f"🚨 *بلاغ جديد من نظام المستشفى*\n\n"
      f"🎟️ *رقم البلاغ:* {data.get('ticket_number', '-')}\n"
      f"📁 *رقم الملف:* {data.get('file_number', '-')}\n"
      f"👤 *اسم البلاغ:* {data.get('patient_name')}\n"
      f"⚙️ *الموضوع:* {data.get('requested_service')}\n"
      f"🏥 *القسم المعني:* {data.get('service_name')}\n"
      f"👨‍⚕️ *الشخص المعني:* {data.get('employee_name')}\n"
      f"📅 *الوقت:* {data.get('record_date')} - {data.get('record_time')}"
  )

  payload = {
      "messaging_product": "whatsapp",
      "to": WHATSAPP_RECIPIENT,
      "type": "text",
      "text": {"body": message_text},
  }

  try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print("WhatsApp API Response:", response.json())
  except Exception as e:
    print("Error sending WhatsApp notification:", e)


# =========================
# Main Page
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    data = request.form
    ticket_number = data.get("ticket_number")
    patient_name = data.get("patient_name")
    national_id = data.get("national_id", "0000000000")
    file_number = data.get("file_number", "-")
    patient_phone = data.get("patient_phone", "0500000000")
    requested_service = data.get("requested_service")
    service_name = data.get("service_name")
    employee_name = data.get("employee_name")
    record_date = data.get("record_date")
    record_time = data.get("record_time")

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

      # إرسال إشعار الواتساب تلقائياً من السيرفر بعد نجاح الحفظ
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
