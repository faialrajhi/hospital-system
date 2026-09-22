from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
from datetime import datetime
import os

app = Flask(__name__)

# =========================================================
# إعدادات Supabase
# =========================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# إعدادات Twilio
# =========================================================

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# رقم Twilio الخاص بالـ SMS
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# رقم Twilio الخاص بالـ WhatsApp
# مثال:
# whatsapp:+14155238886
#
# إذا كنت تستخدم WhatsApp Sandbox في Twilio
# ضع رقم الـ Sandbox هنا.
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM")


# =========================================================
# دالة إنشاء اتصال Twilio
# =========================================================

def get_twilio_client():

    if not TWILIO_ACCOUNT_SID:
        raise Exception("TWILIO_ACCOUNT_SID غير موجود في Render.")

    if not TWILIO_AUTH_TOKEN:
        raise Exception("TWILIO_AUTH_TOKEN غير موجود في Render.")

    return TwilioClient(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN
    )


# =========================================================
# تحويل رقم الجوال السعودي إلى صيغة دولية
# =========================================================

def normalize_saudi_phone(phone):

    if not phone:
        return None

    phone = str(phone).strip()

    # إزالة المسافات والرموز
    phone = (
        phone
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    # 05xxxxxxxx
    if phone.startswith("05") and len(phone) == 10:
        return "+966" + phone[1:]

    # 5xxxxxxxx
    if phone.startswith("5") and len(phone) == 9:
        return "+966" + phone

    # 9665xxxxxxxx
    if phone.startswith("9665") and len(phone) == 12:
        return "+" + phone

    # +9665xxxxxxxx
    if phone.startswith("+9665") and len(phone) == 13:
        return phone

    # إذا كان رقمًا دوليًا آخر
    if phone.startswith("+"):
        return phone

    return None


# =========================================================
# إنشاء رسالة المريض
# =========================================================

def build_patient_message(
    patient_name,
    ticket_number,
    requested_service,
    service_name
):

    patient_name = patient_name or "المريض"
    ticket_number = ticket_number or "-"
    requested_service = requested_service or "-"
    service_name = service_name or "-"

    return (
        f"مرحباً {patient_name}،\n\n"
        f"تم تسجيل طلبك بنجاح في وحدة الدعم المساندة.\n\n"
        f"رقم التذكرة: {ticket_number}\n"
        f"الخدمة المطلوبة: {requested_service}\n"
        f"القسم: {service_name}\n\n"
        f"يرجى الاحتفاظ برقم التذكرة.\n"
        f"شكراً لتواصلك معنا."
    )


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        new_record = {
            "patient_name": request.form.get("patient_name"),
            "national_id": request.form.get("national_id"),
            "file_number": request.form.get("file_number"),
            "patient_phone": request.form.get("patient_phone"),
            "requested_service": request.form.get("requested_service"),
            "service_name": request.form.get("service_name"),
            "employee_name": request.form.get("employee_name"),
            "record_date": request.form.get("record_date") or current_date,
            "record_time": request.form.get("record_time") or current_time
        }

        try:

            response = (
                supabase
                .table("patient_records")
                .insert(new_record)
                .execute()
            )

            print("Insert Response:", response)

        except Exception as e:

            print(
                "Error saving to Supabase:",
                str(e)
            )

        return redirect(url_for("index"))

    # =====================================================
    # جلب السجلات
    # =====================================================

    try:

        response = (
            supabase
            .table("patient_records")
            .select("*")
            .execute()
        )

        records = (
            response.data
            if response.data
            else []
        )

    except Exception as e:

        print(
            "Error fetching from Supabase:",
            str(e)
        )

        records = []

    return render_template(
        "index.html",
        records=records
    )


# =========================================================
# تصدير Excel
# =========================================================

@app.route("/export-excel")
def export_excel():

    return "تم طلب تصدير السجلات إلى إكسل بنجاح."


# =========================================================
# إرسال SMS عبر Twilio
# =========================================================

@app.route("/send-sms", methods=["POST"])
def send_sms():

    try:

        data = request.get_json(silent=True) or {}

        phone = data.get("phone")
        patient_name = data.get("patient_name")
        ticket_number = data.get("ticket_number")
        requested_service = data.get("requested_service")
        service_name = data.get("service_name")

        # -----------------------------------------------
        # التحقق من الرقم
        # -----------------------------------------------

        normalized_phone = normalize_saudi_phone(phone)

        if not normalized_phone:

            return jsonify({
                "success": False,
                "message": "رقم الجوال غير صحيح. استخدمي 05xxxxxxxx."
            }), 400

        # -----------------------------------------------
        # التحقق من رقم Twilio
        # -----------------------------------------------

        if not TWILIO_PHONE_NUMBER:

            return jsonify({
                "success": False,
                "message": "TWILIO_PHONE_NUMBER غير موجود في إعدادات Render."
            }), 500

        # -----------------------------------------------
        # إنشاء الرسالة
        # -----------------------------------------------

        message_body = build_patient_message(
            patient_name,
            ticket_number,
            requested_service,
            service_name
        )

        # -----------------------------------------------
        # إرسال SMS
        # -----------------------------------------------

        client = get_twilio_client()

        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=normalized_phone
        )

        print(
            "SMS sent successfully:",
            message.sid
        )

        return jsonify({
            "success": True,
            "message": "تم إرسال الرسالة النصية بنجاح.",
            "sid": message.sid
        })

    except Exception as e:

        print(
            "Error sending SMS via Twilio:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": f"فشل إرسال SMS: {str(e)}"
        }), 500


# =========================================================
# إرسال WhatsApp عبر Twilio
# =========================================================

@app.route("/send-whatsapp", methods=["POST"])
def send_whatsapp():

    try:

        data = request.get_json(silent=True) or {}

        phone = data.get("phone")
        patient_name = data.get("patient_name")
        ticket_number = data.get("ticket_number")
        requested_service = data.get("requested_service")
        service_name = data.get("service_name")

        # -----------------------------------------------
        # التحقق من الرقم
        # -----------------------------------------------

        normalized_phone = normalize_saudi_phone(phone)

        if not normalized_phone:

            return jsonify({
                "success": False,
                "message": "رقم الجوال غير صحيح. استخدمي 05xxxxxxxx."
            }), 400

        # -----------------------------------------------
        # التحقق من WhatsApp From
        # -----------------------------------------------

        if not TWILIO_WHATSAPP_FROM:

            return jsonify({
                "success": False,
                "message": (
                    "متغير TWILIO_WHATSAPP_FROM غير موجود "
                    "في إعدادات Render."
                )
            }), 500

        # -----------------------------------------------
        # إنشاء الرسالة
        # -----------------------------------------------

        message_body = build_patient_message(
            patient_name,
            ticket_number,
            requested_service,
            service_name
        )

        # -----------------------------------------------
        # إرسال WhatsApp
        # -----------------------------------------------

        client = get_twilio_client()

        message = client.messages.create(
            body=message_body,
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{normalized_phone}"
        )

        print(
            "WhatsApp sent successfully:",
            message.sid
        )

        return jsonify({
            "success": True,
            "message": "تم إرسال رسالة WhatsApp بنجاح.",
            "sid": message.sid
        })

    except Exception as e:

        print(
            "Error sending WhatsApp via Twilio:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": f"فشل إرسال WhatsApp: {str(e)}"
        }), 500


# =========================================================
# تشغيل التطبيق
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
