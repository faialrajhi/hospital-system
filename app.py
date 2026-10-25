import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'support_unit_secret_key_123')

# إعدادات اتصال Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://urnawuapfkhxvqvepzit.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVybmF3dWFwZmtoeHZxdmVweml0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgwOTU0MTAsImV4cCI6MjEwMzY3MTQxMH0.IfhRYq5D8072nOzJOMCW1A9c7i93D4mCd2I5Q3TJ-Kc")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# بيانات المستخدمين والصلاحيات مع تحديد الاسم الكامل للمدير وباقي الموظفين
USERS = {
    "turky": {"password": "123", "role": "admin", "title": "مدير النظام", "can_edit": True, "full_name": "تركي محمد المولد"},
    "mohd": {"password": "123", "role": "supervisor", "title": "مشرف أول", "can_edit": True, "full_name": "محمد"},
    "raja": {"password": "123", "role": "supervisor", "title": "مشرف", "can_edit": False, "full_name": "رجا"},
    "hosam": {"password": "123", "role": "supervisor", "title": "مشرف", "can_edit": False, "full_name": "حسام"},
    "abdullah": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True, "full_name": "عبدالله"},
    "ahmed": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True, "full_name": "أحمد"},
    "ebtisam": {"password": "123", "role": "employee", "title": "موظفة", "can_edit": True, "full_name": "ابتسام"},
    "nozha": {"password": "123", "role": "employee", "title": "موظفة", "can_edit": True, "full_name": "نزهة"},
    "khaled": {"password": "123", "role": "employee", "title": "موظف", "can_edit": True, "full_name": "خالد"}
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
            # تخزين الاسم الكامل في الجلسة لاستخدامه في العرض والملاحظات
            session['full_name'] = USERS[username].get("full_name", username)
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
        
    # جلب الاسم الكامل للمستخدم المسجل حالياً
    logged_employee = session.get('full_name', session.get('user'))
    user_role = session.get('role', 'employee')
    user_title = session.get('user_title', 'موظف')
    can_edit = session.get('can_edit', False)
    
    if request.method == 'POST' and can_edit:
        action_type = request.form.get('action_type')
        
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
            "status": "مغلق راضي"  # الحالة الافتراضية للبلاغات الجديدة
        }
        
        try:
            # 1. حفظ السجل في قاعدة بيانات Supabase
            supabase.table("patient_records").insert(record_data).execute()
            
            # 2. إرسال الإشعار آلياً للقروب عبر Green-API مع فحص النتائج
            if action_type == 'save_and_send':
                id_instance = os.environ.get("GREEN_API_ID_INSTANCE")
                api_token = os.environ.get("GREEN_API_TOKEN")
                chat_id = os.environ.get("WHATSAPP_GROUP_ID")
                
                print(f"DEBUG -> Instance: {id_instance}, ChatID: {chat_id}")
                
                if id_instance and api_token and chat_id:
                    url = f"https://api.green-api.com/waInstance{id_instance}/sendMessage/{api_token}"
                    
                    message_text = (
                        f"*بلاغ جديد*\n\n"
                        f"*رقم البلاغ:* {ticket_number}\n"
                        f"*رقم الملف:* {file_number}\n"
                        f"*اسم المبلغ:* {patient_name}\n"
                        f"*الموضوع:* {requested_service}\n"
                        f"*القسم المعني:* {service_name}\n"
                        f"*الشخص المعني:* {concerned_person}\n"
                        f"*الموظف المسؤول:* {logged_employee}\n"
                        f"*التاريخ والوقت:* {record_date} {record_time}"
                    )
                    
                    payload = {
                        "chatId": chat_id,
                        "message": message_text
                    }
                    
                    response = requests.post(url, json=payload)
                    print(f"GREEN_API_STATUS: {response.status_code}")
                    print(f"GREEN_API_TEXT: {response.text}")
                else:
                    print("ERROR: Missing Green-API environment variables in Render!")
                    
        except Exception as e:
            print(f"Error saving or sending record: {e}")
            
        return redirect(url_for('index'))
        
    # جلب السجلات
    try:
        response = supabase.table("patient_records").select("*").order("id", desc=True).execute()
        records = response.data if response.data else []
    except Exception as e:
        print(f"Error fetching records: {e}")
        records = []
        
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

@app.route('/save-note', methods=['POST'])
def save_note():
    if 'user' not in session:
        return jsonify({'success': False, 'message': 'غير مصرح'}), 401
        
    data = request.json
    record_id = data.get('record_id')
    new_action_note = data.get('action_notes')
    status = data.get('status')
    
    logged_user = session.get('full_name', session.get('user', 'مستخدم'))
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
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
