from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from datetime import datetime, timezone, timedelta
import os
from supabase import create_client, Client
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # استبدليها بمفتاح سري خاص بك

# إعدادات اتصال Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY and SUPABASE_URL != "YOUR_SUPABASE_URL":
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        patient_name = request.form.get("patient_name")
        national_id = request.form.get("national_id")
        file_number = request.form.get("file_number")
        requested_service = request.form.get("requested_service")  # استقبال الخدمة المطلوبة الجديدة
        service_name = request.form.get("service_name")
        employee_name = request.form.get("employee_name")
        
        ksa_tz = timezone(timedelta(hours=3))
        now_ksa = datetime.now(ksa_tz)
        
        record_date = request.form.get("record_date") or now_ksa.strftime('%Y-%m-%d')
        record_time = request.form.get("record_time") or now_ksa.strftime('%H:%M')

        if supabase:
            try:
                supabase.table("records").insert({
                    "patient_name": patient_name,
                    "national_id": national_id,
                    "file_number": file_number,
                    "requested_service": requested_service,  # حفظ الحقل في قاعدة البيانات
                    "service_name": service_name,
                    "employee_name": employee_name,
                    "record_date": record_date,
                    "record_time": record_time,
                }).execute()
                flash("تم حفظ السجل بنجاح!", "success")
            except Exception as e:
                print(f"Error saving to Supabase: {e}")

        return redirect(url_for("index"))

    # جلب البيانات للعرض في القوائم والجدول
    services = []
    employees = []
    records = []
    
    if supabase:
        try:
            services_res = supabase.table("services").select("*").execute()
            services = services_res.data if services_res.data else []
            
            employees_res = supabase.table("employees").select("*").execute()
            employees = employees_res.data if employees_res.data else []
            
            records_res = supabase.table("records").select("*").order("id", desc=True).limit(50).execute()
            records = records_res.data if records_res.data else []
        except Exception as e:
            print(f"Error fetching data: {e}")

    return render_template("index.html", services=services, employees=employees, records=records)

@app.route("/preview")
def preview_data():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    records = []
    services = []
    employees = []
    
    if supabase:
        try:
            query = supabase.table("records").select("*")
            if start_date:
                query = query.gte("record_date", start_date)
            if end_date:
                query = query.lte("record_date", end_date)
            res = query.order("id", desc=True).execute()
            records = res.data if res.data else []
            
            services = supabase.table("services").select("*").execute().data or []
            employees = supabase.table("employees").select("*").execute().data or []
        except Exception as e:
            print(f"Error previewing data: {e}")
            
    return render_template("index.html", services=services, employees=employees, records=records)

@app.route("/export")
def export_excel():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    records = []
    if supabase:
        try:
            query = supabase.table("records").select("*")
            if start_date:
                query = query.gte("record_date", start_date)
            if end_date:
                query = query.lte("record_date", end_date)
            res = query.order("id", desc=True).execute()
            records = res.data if res.data else []
        except Exception as e:
            print(f"Error exporting data: {e}")
            
    if not records:
        df = pd.DataFrame(columns=["الاسم", "الهوية", "رقم الملف", "الخدمة المطلوبة", "القسم", "الموظف", "التاريخ", "الوقت"])
    else:
        df = pd.DataFrame(records)
        column_mapping = {
            "patient_name": "الاسم",
            "national_id": "الهوية",
            "file_number": "رقم الملف",
            "requested_service": "الخدمة المطلوبة",
            "service_name": "القسم",
            "employee_name": "الموظف",
            "record_date": "التاريخ",
            "record_time": "الوقت"
        }
        df = df.rename(columns=column_mapping)
        available_cols = [col for col in ["الاسم", "الهوية", "رقم الملف", "الخدمة المطلوبة", "القسم", "الموظف", "التاريخ", "الوقت"] if col in df.columns]
        df = df[available_cols]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='السجلات')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='patient_records.xlsx'
    )

if __name__ == "__main__":
    app.run(debug=True)
