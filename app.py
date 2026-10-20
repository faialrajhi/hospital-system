import os
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'support_unit_secret_key_123')

# إعدادات اتصال Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://your-supabase-url.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "your-supabase-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# بيانات المستخدمين والصلاحيات
USERS = {
    "turky": {"password": "123", "role": "Admin", "can_edit": True},
    "mohd": {"password": "123", "role": "Supervisor", "can_edit": True},
    "raja": {"password": "123", "role": "Supervisor", "can_edit": False},
    "hosam": {"password": "123", "role": "Supervisor", "can_edit": False},
    "ibrahim": {"password": "123", "role": "Employee", "can_edit": True},
    "saleh": {"password": "123", "role": "Employee", "can_edit": True},
    "ahlam": {"password": "123", "role": "Employee", "can_edit": True},
    "maatouq": {"password": "123", "role": "Employee", "can_edit": True},
    "saleem": {"password": "123", "role": "Employee", "can_edit": True},
    "fowzi": {"password": "123", "role": "Employee", "can_edit": True},
    "rami": {"password": "123", "role": "Employee", "can_edit": True}
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        password = request.form.get('password')
        
        if username in USERS and USERS[username]["password"] == password:
            session['user'] = username
            session['role'] = USERS[username]["role"]
            session['can_edit'] = USERS[username]["can_edit"]
            return redirect(url_for('index'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
        
    logged_employee = session['user']
    can_edit = session.get('can_edit', False)
    
    if request.method == 'POST' and can_edit:
        action_type = request.form.get('action_type') # يحدد نوع الزر (حفظ فقط أم حفظ وإرسال)
        
        patient_name = request.form.get('patient_name')
        file_number = request.form.get('file_number')
        national_id = request.form.get('national_id')
        patient_phone = request.form.get('patient_phone')
        requested_service = request.form.get('service_type')
        service_name = request.form.get('department')
        action_notes = request.form.get('notes')
        record_date = request.form.get('record_date') or datetime.now().strftime('%Y-%m-%d')
        record_time = request.form.get('record_time') or datetime.now().strftime('%H:%M:%S')
        
        # تجهيز البيانات بأسماء الأعمدة المطابقة لـ Supabase 100%
        record_data = {
            "patient_name": patient_name,
            "file_number": file_number,
            "national_id": national_id,
            "patient_phone": patient_phone,
            "requested_service": requested_service,
            "service_name": service_name,
            "action_notes": action_notes,
            "employee_name": logged_employee,
            "record_date": record_date,
            "record_time": record_time
        }
        
        try:
            # حفظ البيانات في Supabase
            supabase.table("patient_records").insert(record_data).execute()
            
            # إذا ضغط المستخدم على "حفظ وإرسال للقروب" ينفذ الإرسال للقروب
            if action_type == 'save_and_send':
                # يمكن ربطه بشرائح إرسال الواتساب/القروب مستقبلاً
                pass
                
        except Exception as e:
            print(f"Error saving record: {e}")
            
        return redirect(url_for('index'))
        
    # جلب السجلات للعرض
    try:
        response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
        records = response.data if response.data else []
    except Exception as e:
        print(f"Error fetching records: {e}")
        records = []
        
    return render_template('index.html', records=records, logged_employee=logged_employee, can_edit=can_edit)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
