from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
import os

app = Flask(__name__)

# بيانات الاتصال بـ Supabase (يفضل استخدام Environment Variables في الاستضافة)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "ضعي_رابط_مشروعك_هنا")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "ضعي_مفتاح_api_هنا")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_record = {
            'patient_name': request.form.get('patient_name'),
            'national_id': request.form.get('national_id'),
            'file_number': request.form.get('file_number'),
            'requested_service': request.form.get('requested_service'),
            'service_name': request.form.get('service_name'),
            'employee_name': request.form.get('employee_name'),
            'record_date': request.form.get('record_date'),
            'record_time': request.form.get('record_time')
        }
        # إدخال السجل مباشرة في جدول Supabase
        supabase.table("patient_records").insert(new_record).execute()
        return redirect(url_for('index'))

    # جلب السجلات مرتبة من الأحدث للأقدم
    response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
    records = response.data if response.data else []

    return render_template('index.html', records=records)

@app.route('/export_excel')
def export_excel():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
