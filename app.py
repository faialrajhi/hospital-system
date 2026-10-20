import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
    "turky": {"password": "123", "role": "admin", "title": "مدير النظام", "can_edit": True},
    "mohd": {"password": "123", "role": "supervisor", "title": "مشرف أول", "can_edit": True},
    "raja": {"password": "123", "role": "supervisor", "title": "مشرف", "can_edit": False},
    "hosam": {"password": "123", "role": "supervisor", "title": "مشرف", "can_edit": False},
    "ibrahim": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True},
    "saleh": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True},
    "ahlam": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True},
    "maatouq": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True},
    "saleem": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True},
    "fowzi": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True},
    "rami": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True}
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
            session['user_title'] = USERS[username]["title"]
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
    user_role = session.get('role', 'employee')
    user_title = session.get('user_title', 'موظف')
    can_edit = session.get('can_edit', False)
    
    if request.method == 'POST' and can_edit:
        action_type = request.form.get('action_type') # حفظ فقط أو حفظ وإرسال للقروب
        
        ticket_number = request.form.get('ticket_number')
        file_number = request.form.get('file_number')
        patient_name = request.form.get('patient_name')
        requested_service = request.form.get('requested_service')
        service_name = request.form.get('service_name')
        concerned_person = request.form.get('concerned_person')
        record_date = request.form.get('record_date') or datetime.now().strftime('%Y-%m-%d')
        record_time = request.form.get('record_time') or datetime.now().strftime('%H:%M:%S')
        
        record_data = {
            "ticket_number": ticket_number,
            "file_number": file_number,
            "patient_name": patient_name,
            "requested_service": requested_service,
            "service_name": service_name,
            "concerned_person": concerned_person,
            "employee_name": logged_employee,
            "record_date": record_date,
            "record_time": record_time,
            "status": "new"
        }
        
        try:
            supabase.table("patient_records").insert(record_data).execute()
            if action_type == 'save_and_send':
                # مكان ربط إرسال الواتساب/القروب مستقبلاً
                pass
        except Exception as e:
            print(f"Error saving record: {e}")
            
        return redirect(url_for('index'))
        
    # جلب السجلات
    try:
        response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
        records = response.data if response.data else []
    except Exception as e:
        print(f"Error fetching records: {e}")
        records = []
        
    # حساب رقم البلاغ التالي
    next_ticket_number = "1"
    if records:
        try:
            latest_ticket = int(records[0].get('ticket_number', 0))
            next_ticket_number = str(latest_ticket + 1)
        except:
            pass

    return render_template('index.html', 
                           records=records, 
                           logged_employee=logged_employee, 
                           user_role=user_role,
                           user_title=user_title,
                           can_edit=can_edit,
                           next_ticket_number=next_ticket_number)

# مسار حفظ الملاحظات والتوجيهات من النافذة المنبثقة أو تحديث الحالة مباشرة
@app.route('/save-note', methods=['POST'])
def save_note():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 401
        
    data = request.json
    record_id = data.get('record_id')
    new_action_note = data.get('action_notes')
    status = data.get('status')
    
    logged_user = session.get('user', 'مستخدم')
    role_title = session.get('user_title', 'موظف')
    current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    update_data = {}
    
    if status:
        update_data['status'] = status
        
    if new_action_note:
        try:
            res = supabase.table("patient_records").select("action_notes").eq("id", record_id).execute()
            old_notes = res.data[0].get('action_notes', '') if res.data and res.data[0] else ''
            
            formatted_entry = f"[{current_time_str}] {logged_user} ({role_title}): {new_action_note}"
            
            if old_notes and str(old_notes).strip() and str(old_notes) != 'None':
                combined_notes = formatted_entry + "\n-------------------\n" + str(old_notes)
            else:
                combined_notes = formatted_entry
                
            update_data['action_notes'] = combined_notes
        except Exception as e:
            update_data['action_notes'] = f"[{current_time_str}] {logged_user} ({role_title}): {new_action_note}"

    try:
        supabase.table("patient_records").update(update_data).eq("id", record_id).execute()
        return jsonify({
            'success': True, 
            'updated_notes': update_data.get('action_notes', '')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/export-excel')
def export_excel():
    # دالة التصدير إن وجدت لديك
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
