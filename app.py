import os
from flask import Flask, render_template, request, redirect, url_for, send_file
from supabase import create_client
import pandas as pd
import openpyxl
from datetime import datetime

app = Flask(__name__)

# جلب بيانات الاتصال من متغيرات البيئة في Render
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key) if url and key else None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        national_id = request.form.get('national_id')
        file_number = request.form.get('file_number')
        service = request.form.get('service')
        employee_name = request.form.get('employee_name')
        
        # الوقت والتاريخ الحالي بتوقيت السعودية أو النظام
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if supabase:
            try:
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
    
    # جلب السجلات لعرضها في الجدول
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
    if supabase:
        try:
            response = supabase.table("records").select("*").execute()
            data = response.data
            if data:
                df = pd.DataFrame(data)
                file_path = "patient_records.xlsx"
                df.to_excel(file_path, index=False, engine='openpyxl')
                return send_file(file_path, as_attachment=True)
        except Exception as e:
            print(f"Error exporting excel: {e}")
            
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
