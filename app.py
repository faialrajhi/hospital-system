from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client
from twilio.rest import Client as TwilioClient
import os

app = Flask(__name__)

# إعدادات اتصال Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "رابط_السوبابيس_هنا")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "مفتاح_السوبابيس_هنا")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# بيانات تويليو
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # استقبال البيانات من النموذج وحفظها
        new_record = {
            'patient_name': request.form.get('patient_name'),
            'national_id': request.form.get('national_id'),
            'file_number': request.form.get('file_number'),
            'patient_phone': request.form.get('patient_phone'),
            'requested_service': request.form.get('requested_service'),
            'service_name': request.form.get('service_name'),
            'employee_name': request.form.get('employee_name'),
            'record_date': request.form.get('record_date'),
            'record_time': request.form.get('record_time')
        }
        
        try:
            supabase.table("patient_records").insert(new_record).execute()
        except Exception as e:
            print("Error saving to Supabase:", e)
            
        return redirect(url_for('index'))
    
    # استرجاع وعرض جميع السجلات القديمة والجديدة من جدول patient_records
    try:
        response = supabase.table("patient_records").select("*").execute()
        records = response.data if response.data else []
    except Exception as e:
        print("Error fetching from Supabase:", e)
        records = []
        
    return render_template('index.html', records=records)

@app.route('/export-excel')
def export_excel():
    return "تم طلب تصدير السجلات إلى إكسل بنجاح."

# مسار إرسال الرسائل النصية عبر Twilio
@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get('phone')
    
    if phone and not phone.startswith('+'):
        if phone.startswith('05'):
            phone = '+966' + phone[1:]
        else:
            phone = '+' + phone

    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body="عزيزي المريض، تم تسجيل تفاصيل تجربتك بنجاح في النظام. شكراً لثقتك بنا.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        return jsonify({
            'success': True, 
            'message': f'تم إرسال الرسالة النصية بنجاح إلى الرقم: {phone}'
        })
    except Exception as e:
        print("Error sending SMS via Twilio:", e)
        return jsonify({
            'success': False,
            'message': f'فشل إرسال الرسالة: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
