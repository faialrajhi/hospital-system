import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# الاتصال بـ Supabase باستخدام متغيرات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # استقبال البيانات من النموذج
        patient_name = request.form.get('patient_name')
        national_id = request.form.get('national_id')
        file_number = request.form.get('file_number')
        service = request.form.get('service')
        employee_name = request.form.get('employee_name')
        
        # الحصول على التاريخ والوقت الحالي بتوقيت السعودية/المحلي
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if supabase:
            try:
                # إدخال البيانات في جدول Supabase (تأكدي أن اسم الجدول لديك هو records أو تعديل الاسم هنا)
                supabase.table("records").insert({
                    "patient_name": patient_name,
                    "national_id": national_id,
                    "file_number": file_number,
                    "service": service,
                    "employee_name": employee_name,
                    "created_at": current_time
                }).execute()
            except Exception as e:
                print(f"Error saving to Supabase: {e}")

        return redirect(url_for('index'))

    # جلب السجلات لعرضها في الجدول أسفل الصفحة
    records = []
    if supabase:
        try:
            response = supabase.table("records").select("*").order("created_at", desc=True).execute()
            records = response.data
        except Exception as e:
            print(f"Error fetching from Supabase: {e}")

    return render_template('index.html', records=records)

@app.route('/export_excel')
def export_excel():
    # تصدير السجلات إلى ملف Excel
    if supabase:
        try:
            response = supabase.table("records").select("*").execute()
            data = response.data
            if data:
                df = pd.DataFrame(data)
                file_path = "hospital_records.xlsx"
                df.to_excel(file_path, index=False)
                return send_file(file_path, as_attachment=True)
        except Exception as e:
            print(f"Error exporting excel: {e}")
    return "لا توجد بيانات للتصدير أو حدث خطأ.", 400

if __name__ == '__main__':
    app.run(debug=True)
