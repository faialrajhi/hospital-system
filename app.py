from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "hospital_reception_secret_key"

# بيانات الربط مع Supabase
SUPABASE_URL = "https://urnawuapfkhxvqvepzit.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVybmF3dWFwZmtoeHZxdmVweml0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgwOTU0MTAsImV4cCI6MjEwMzY3MTQxMH0.IfhRYq5D8072nOzJOMCW1A9c7i93D4mCd2I5Q3TJ-Kc"
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None

@app.route('/')
def index():
    services = [{'name': 'أطباء الباطنة'}, {'name': 'تمريض الباطنة'}]
    employees = [{'name': 'صالح حنيف'}, {'name': 'أحلام'}, {'name': 'محمد سعد'}]
    records = []

    if supabase:
        try:
            res = supabase.table('records').select('*').order('id', desc=True).execute()
            records = res.data
        except Exception as e:
            print("خطأ في جلب البيانات:", e)

    return render_template('index.html', services=services, employees=employees, records=records)

@app.route('/add_record', methods=['POST'])
def add_record():
    patient_name = request.form.get('patient_name')
    national_id = request.form.get('national_id')
    file_number = request.form.get('file_number')
    service_name = request.form.get('service_name')
    employee_name = request.form.get('employee_name')

    if supabase:
        try:
            supabase.table('records').insert({
                'patient_name': patient_name,
                'national_id': national_id,
                'file_number': file_number,
                'service_name': service_name,
                'employee_name': employee_name
            }).execute()
        except Exception as e:
            print("خطأ أثناء الإضافة إلى Supabase:", e)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)