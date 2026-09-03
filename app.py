import os
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from supabase import Client, create_client
import pandas as pd
import io
from datetime import datetime

app = Flask(_name_)
app.secret_key = "hospital_secret_key"

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key) if url and key else None

SERVICES_LIST = [
    {"name": "أطباء الباطنة"},
    {"name": "تمريض الباطنة"},
    {"name": "أطباء الجراحة"},
    {"name": "تمريض الجراحة"},
    {"name": "أطباء العظام"},
    {"name": "تمريض العظام"},
    {"name": "أطباء المخ والأعصاب"},
    {"name": "تمريض المخ والأعصاب"},
    {"name": "صيدلية"},
    {"name": "الأشعة"},
    {"name": "المعلومات الصحية"},
    {"name": "مكتب الدخول"},
    {"name": "الصحة الرقمية"},
    {"name": "إدارة المرافق"},
    {"name": "الطب المنزلي"},
    {"name": "الوفيات"},
    {"name": "الخدمة الاجتماعية"},
    {"name": "العلاج الطبيعي"},
    {"name": "أطباء النفسية"},
    {"name": "تمريض النفسية"},
    {"name": "الإمداد"},
    {"name": "المختبر"},
    {"name": "إدارة القبول"},
]

EMPLOYEES_LIST = [
    {"name": "صالح حنيف"},
    {"name": "ابراهيم بخاري"},
    {"name": "احلام هوساوي"},
    {"name": "معتوق سيف"},
    {"name": "تركي عبدالعزيز"},
    {"name": "سليم الشريف"},
    {"name": "فوزي بليلة"},
    {"name": "رامي اللقماني"},
    {"name": "متدرب"},
    {"name": "تمهير"},
    {"name": "تطوع"}
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        patient_name = request.form.get("patient_name")
        national_id = request.form.get("national_id")
        file_number = request.form.get("file_number")
        service_name = request.form.get("service_name")
        employee_name = request.form.get("employee_name")
        record_date = request.form.get("record_date")
        record_time = request.form.get("record_time")

        if supabase:
            try:
                supabase.table("records").insert({
                    "patient_name": patient_name,
                    "national_id": national_id,
                    "file_number": file_number,
                    "service_name": service_name,
                    "employee_name": employee_name,
                    "record_date": record_date,
                    "record_time": record_time,
                }).execute()
                flash("تم حفظ السجل بنجاح!", "success")
            except Exception as e:
                print(f"Error saving to Supabase: {e}")

        return redirect(url_for("index"))
    
    # جلب السجلات للرئيسية مرتبة تنازلياً حسب التاريخ والوقت
    records = []
    if supabase:
        try:
            response = supabase.table("records").select("*").order("record_date", desc=True).order("record_time", desc=True).limit(50).execute()
            records = response.data
        except Exception as e:
            print(f"Error fetching from Supabase: {e}")

    return render_template(
        "index.html",
        records=records,
        services=SERVICES_LIST,
        employees=EMPLOYEES_LIST
    )

# دالة لتصفية وجلب السجلات مع ترتيبها تنازلياً حسب التاريخ والوقت
def get_filtered_records(start_date, end_date):
    if not supabase:
        return []
    try:
        # جلب البيانات وترتيبها مباشرة من قاعدة البيانات
        response = supabase.table("records").select("*").order("record_date", desc=True).order("record_time", desc=True).execute()
        all_data = response.data if response.data else []
        
        if not start_date and not end_date:
            return all_data
            
        filtered = []
        for row in all_data:
            r_date = row.get("record_date")
            if not r_date:
                continue
            
            match = True
            if start_date and r_date < start_date:
                match = False
            if end_date and r_date > end_date:
                match = False
                
            if match:
                filtered.append(row)
        return filtered
    except Exception as e:
        print(f"Error filtering records: {e}")
        return []

@app.route("/preview")
def preview_data():
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    
    records = get_filtered_records(start_date, end_date)

    return render_template(
        "preview_data.html",
        records=records,
        start_date=start_date,
        end_date=end_date
    )

@app.route("/export_excel")
def export_excel():
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    
    try:
        data = get_filtered_records(start_date, end_date)
        
        if not data:
            df = pd.DataFrame(columns=["اسم المريض", "رقم الهوية", "رقم الملف", "الخدمة المقدمة", "اسم الموظف", "التاريخ", "الوقت"])
        else:
            df = pd.DataFrame(data)
        
        column_mapping = {
            "patient_name": "اسم المريض",
            "national_id": "رقم الهوية",
            "file_number": "رقم الملف",
            "service_name": "الخدمة المقدمة",
            "service": "الخدمة المقدمة",
            "employee_name": "اسم الموظف",
            "record_date": "التاريخ",
            "record_time": "الوقت"
        }
        df = df.rename(columns=column_mapping)
        
        available_cols = [c for c in ["اسم المريض", "رقم الهوية", "رقم الملف", "القسم", "اسم الموظف", "التاريخ", "الوقت"] if c in df.columns]
        if available_cols:
            df = df[available_cols]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='السجلات')
        output.seek(0)

        filename = f"hospital_records_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"Error exporting excel: {e}")
        return redirect(url_for("index"))

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000)
