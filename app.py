import os
from flask import Flask, render_template, request, jsonify
import requests
from supabase import create_client, Client

app = Flask(__name__)

# دالة آمنة للاتصال بـ Supabase
def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

def send_whatsapp_notification(ticket_number):
    token = os.environ.get("WHATSAPP_TOKEN")
    phone_id = os.environ.get("WHATSAPP_PHONE_ID")
    recipient = os.environ.get("WHATSAPP_RECIPIENT", "966565142164")

    if not token or not phone_id:
        print("WhatsApp credentials missing in environment variables.")
        return None

    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
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
        print("WhatsApp Response:", response.json())
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
        
        supabase_client = get_supabase()
        if not supabase_client:
            return jsonify({"status": "error", "message": "Supabase credentials missing"}), 500

        record_data = {
            "ticket_number": data.get('ticket_number'),
            "patient_name": data.get('patient_name'),
            "file_number": data.get('file_number'),
            "requested_service": data.get('requested_service'),
            "service_name": data.get('service_name'),
            "employee_name": data.get('employee_name'),
            "record_date": data.get('record_date'),
            "record_time": data.get('record_time'),
            "action_notes": data.get('action_notes')
        }

        response = supabase_client.table("patient_records").insert(record_data).execute()
        
        # إرسال إشعار الواتساب
        wa_response = send_whatsapp_notification(data.get('ticket_number'))

        return jsonify({
            "status": "success", 
            "message": "تم حفظ البلاغ وإرسال الإشعار بنجاح",
            "whatsapp_response": wa_response
        }), 200

    except Exception as e:
        print("Error saving record:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
