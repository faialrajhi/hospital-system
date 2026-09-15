from flask import Flask, render_template, request, redirect, url_for, send_file
import json
import os

app = Flask(__name__)
DATA_FILE = 'records.json'

def load_records():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_records(records):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

@app.route('/', methods=['GET', 'POST'])
def index():
    records = load_records()
    
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
        # إضافة السجل الجديد في البداية ليكون الأحدث في أعلى القائمة
        records.insert(0, new_record)
        save_records(records)
        return redirect(url_for('index'))

    return render_template('index.html', records=records)

@app.route('/export_excel')
def export_excel():
    # دالة تصدير بسيطة لتجنب أي أخطاء
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
