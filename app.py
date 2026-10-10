import os
from flask import Flask, render_template, request, jsonify
import requests
from supabase import create_client, Client

app = Flask(__name__)

# إعدادات اتصال Supabase من متغيرات البيئة في Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعدادات Meta WhatsApp API
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID")
WHATSAPP_RECIPIENT = os.environ.get("WHATSAPP_RECIPIENT", "966565142164")

def send_whatsapp_notification(ticket_number):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID:
        print("WhatsApp credentials missing in environment variables.")
        return None

    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # استخدام القالب التجريبي المعتمد hello_world لضمان وصول الرسالة فوراً
    payload = {
        "messaging_product": "whatsapp",
        "to": WHATSAPP_RECIPIENT,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US"
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("WhatsApp API Response:", response.json())
        return response.json()
    except Exception as e:
        print("Error sending WhatsApp notification:", str(e))
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_record', methods=['POST'])
def save_record():
    try:
        data = request.form.to_dict()
        
        # استخراج البيانات المدخلة وتجهيزها للتخزين
        ticket_number = data.get('ticket_number')
        patient_name = data.get('patient_name')
        file_number = data.get('file_number')
        requested_service = data.get('requested_service')
        service_name = data.get('service_name')
        employee_name = data.get('employee_name')
        record_date = data.get('record_date')
        record_time = data.get('record_time')
        action_notes = data.get('action_notes')

        # حفظ البيانات في جدول patient_records مع العمود ticket_number
        record_data = {
            "ticket_number": ticket_number,
            "patient_name": patient_name,
            "file_number": file_number,
            "requested_service": requested_service,
            "service_name": service_name,
            "employee_name": employee_name,
            "record_date": record_date,
            "record_time": record_time,
            "action_notes": action_notes
        }

        response = supabase.table("patient_records").insert(record_data).execute()
        
        # إرسال إشعار الواتساب الآلي بعد نجاح الحفظ
        wa_response = send_whatsapp_notification(ticket_number)

        return jsonify({
            "status": "success", 
            "message": "تم حفظ البلاغ وإرسال إشعار الواتساب بنجاح",
            "whatsapp_response": wa_response
        }), 200

    except Exception as e:
        print("Error saving record to Supabase:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
