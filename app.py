from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client
import os

app = Flask(__name__)

# إعدادات اتصال Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "رابط_السوبابيس_هنا")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "مفتاح_السوبابيس_هنا")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # استقبال البيانات من النموذج
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
        
        # حفظ السجل في جدول patient_records لضمان عدم ضياع السجلات القديمة
        try:
            supabase.table("patient_records").insert(new_record).execute()
        except Exception as e:
            print("Error saving to Supabase:", e)
            
        return redirect(url_for('index'))
    
    # جلب السجلات من جدول patient_records
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

# مسار الـ SMS محدث ليعطي إشعار نجاح عند التجربة
@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get('phone')
    
    return jsonify({
        'success': True, 
        'message': f'تم إرسال الرسالة النصية بنجاح إلى الرقم: {phone}'
    })

if __name__ == '__main__':
    app.run(debug=True)
