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

app = Flask(__name__)
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
    
    # جلب التواريخ للفلترة المباشرة من الواجهة إذا وجدت
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
            
            response = query.execute()
            records = response.data
        except Exception as e:
            print(f"Error fetching from Supabase: {e}")

    return render_template(
        "index.html",
        records=records,
        services=SERVICES_LIST,
        employees=EMPLOYEES_LIST,
        start_date=start_date or "",
        end_date=end_date or ""
    )


@app.route("/export_excel")
def export_excel():
    if not supabase:
        return redirect(url_for("index"))
    
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    try:
        query = supabase.table("records").select("*")
        if start_date:
            query = query.gte("record_date", start_date)
        if end_date:
            query = query.lte("record_date", end_date)
            
        response = query.execute()
        data = response.data
        
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
        
        available_cols = [c for c in ["اسم المريض", "رقم الهوية", "رقم الملف", "الخدمة المقدمة", "اسم الموظف", "التاريخ", "الوقت"] if c in df.columns]
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
