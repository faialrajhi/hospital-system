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
    {"name": "محمد سعد"},
    {"name": "أحلام"}
]


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    patient_name = request.form.get("patient_name")
    national_id = request.form.get("national_id")
    file_number = request.form.get("file_number")
    service_name = request.form.get("service_name")
    employee_name = request.form.get("employee_name")

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    if supabase:
      try:
        supabase.table("records").insert({
            "patient_name": patient_name,
            "national_id": national_id,
            "file_number": file_number,
            "service_name": service_name,
            "employee_name": employee_name,
            "record_date": current_date,
            "record_time": current_time,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }).execute()
        flash("تم حفظ السجل بنجاح!", "success")
      except Exception as e:
        print(f"Error saving to Supabase: {e}")

    return redirect(url_for("index"))

  records = []
  if supabase:
    try:
      response = (
          supabase.table("records")
          .select("*")
          .order("created_at", desc=True)
          .execute()
      )
      records = response.data
    except Exception as e:
      print(f"Error fetching from Supabase: {e}")

  return render_template(
      "index.html",
      records=records,
      services=SERVICES_LIST,
      employees=EMPLOYEES_LIST,
  )


@app.route("/export_excel")
def export_excel():
  if not supabase:
    return redirect(url_for("index"))
  try:
    response = supabase.table("records").select("*").execute()
    data = response.data
    if not data:
      return redirect(url_for("index"))
    
    df = pd.DataFrame(data)
    
    # إعادة تسمية الأعمدة لتكون عربية وواضحة في الإكسل
    column_mapping = {
        "patient_name": "اسم المريض",
        "national_id": "رقم الهوية",
        "file_number": "رقم الملف",
        "service_name": "الخدمة المقدمة",
        "employee_name": "اسم الموظف",
        "record_date": "التاريخ",
        "record_time": "الوقت"
    }
    df = df.rename(columns=column_mapping)
    
    # اختيار الأعمدة المطلوبة فقط إذا كانت موجودة
    available_cols = [c for c in column_mapping.values() if c in df.columns]
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
