from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

EXCEL_FILE = 'hospital_records.xlsx'

def init_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=[
            'serial_number', 'patient_name', 'national_id', 'file_number', 
            'requested_service', 'service_name', 'employee_name', 
            'record_date', 'record_time'
        ])
        df.to_excel(EXCEL_FILE, index=False)

init_excel()

def get_period(time_str):
    """تحديد ما إذا كان الوقت في الفترة الصباحية (12 ص إلى 11:59 ص) أو المسائية (12 م إلى 11:59 م)"""
    try:
        hour = int(time_str.split(':')[0])
        minute = int(time_str.split(':')[1])
        total_minutes = hour * 60 + minute
        # من 00:00 (0 دقيقة) إلى 11:59 (719 دقيقة) = فترة صباحية
        # من 12:00 (720 دقيقة) إلى 23:59 = فترة مسائية
        if 0 <= total_minutes < 720:
            return 'MORNING'
        else:
            return 'EVENING'
    except:
        return 'MORNING'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        national_id = request.form.get('national_id')
        file_number = request.form.get('file_number', '-')
        requested_service = request.form.get('requested_service')
        service_name = request.form.get('service_name')
        employee_name = request.form.get('employee_name')
        record_date = request.form.get('record_date') or datetime.now().strftime('%Y-%m-%d')
        record_time = request.form.get('record_time') or datetime.now().strftime('%H:%M')

        # تحديد الفترة الزمنية للسجل الجديد
        current_period = get_period(record_time)

        # قراءة السجلات القديمة لحساب الترقيم التسلسلي بناءً على التاريخ والفترة
        if os.path.exists(EXCEL_FILE):
            df_old = pd.read_excel(EXCEL_FILE)
            df_old = df_old.fillna('-')
        else:
            df_old = pd.DataFrame()

        # حساب الرقم التسلسلي: عدد السجلات السابقة في نفس اليوم ونفس الفترة + 1
        serial_number = 1
        if not df_old.empty and 'record_date' in df_old.columns and 'record_time' in df_old.columns:
            # تصفية السجلات لنفس اليوم
            same_day_df = df_old[df_old['record_date'] == record_date]
            if not same_day_df.empty:
                # تصفية حسب الفترة (صباحية أو مسائية)
                periods = same_day_df['record_time'].apply(get_period)
                same_period_df = same_day_df[periods == current_period]
                serial_number = len(same_period_df) + 1

        new_data = {
            'serial_number': [serial_number],
            'patient_name': [patient_name],
            'national_id': [national_id],
            'file_number': [file_number if file_number else '-'],
            'requested_service': [requested_service],
            'service_name': [service_name],
            'employee_name': [employee_name],
            'record_date': [record_date],
            'record_time': [record_time]
        }
        
        df_new = pd.DataFrame(new_data)
        if not df_old.empty:
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_combined = df_new
            
        df_combined.to_excel(EXCEL_FILE, index=False)
        return redirect(url_for('index'))

    # جلب آخر السجلات للعرض وتحديث الترقيم في العرض إن وجد ناقصاً
    records = []
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df = df.fillna('-')
        records = df.tail(15).iloc[::-1].to_dict('records')

    return render_template('index.html', records=records)

@app.route('/preview')
def preview_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df = df.fillna('-')
        if start_date and end_date:
            df = df[(df['record_date'] >= start_date) & (df['record_date'] <= end_date)]
        records = df.to_dict('records')
    else:
        records = []
        
    return render_template('index.html', records=records)

@app.route('/export')
def export_excel():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        if start_date and end_date:
            df = df[(df['record_date'] >= start_date) & (df['record_date'] <= end_date)]
        
        export_path = 'filtered_records.xlsx'
        df.to_excel(export_path, index=False)
        return send_file(export_path, as_attachment=True)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
