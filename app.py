from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_NAME = "hospital_records.db"

# دالة لإنشاء قاعدة البيانات وجدول السجلات إذا لم يكن موجوداً
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            national_id TEXT,
            file_number TEXT,
            requested_service TEXT,
            service_name TEXT,
            employee_name TEXT,
            record_date TEXT,
            record_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

# استدعاء دالة إنشاء القاعدة عند تشغيل التطبيق
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # لجعل النتائج تُقرأ على شكل قاموس (Dictionary)
    cursor = conn.cursor()

    if request.method == 'POST':
        # استقبال البيانات من النموذج
        patient_name = request.form.get('patient_name')
        national_id = request.form.get('national_id')
        file_number = request.form.get('file_number')
        requested_service = request.form.get('requested_service')
        service_name = request.form.get('service_name')
        employee_name = request.form.get('employee_name')
        record_date = request.form.get('record_date')
        record_time = request.form.get('record_time')

        # حفظ البيانات في قاعدة البيانات المستدامة
        cursor.execute('''
            INSERT INTO records (patient_name, national_id, file_number, requested_service, service_name, employee_name, record_date, record_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_name, national_id, file_number, requested_service, service_name, employee_name, record_date, record_time))
        
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    # جلب جميع السجلات المخزنة لعرضها في الجدول مرتبة من الأحدث للأقدم
    cursor.execute('SELECT * FROM records ORDER BY id DESC')
    records = cursor.fetchall()
    conn.close()

    return render_template('index.html', records=records)

# (ملاحظة: إذا كنتِ تستخدمين مسار لتصدير الإكسل Excel تأكدي أنه يقرأ أيضاً من قاعدة البيانات SQLite بنفس الطريقة)
