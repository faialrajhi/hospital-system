from flask import Flask, render_template, request, jsonify, redirect, url_for
from supabase import create_client, Client
from datetime import datetime
import os
app = Flask(__name__)
# =========================
# Supabase Configuration
# =========================
SUPABASE_URL = os.environ.get(
    "SUPABASE_URL",
    "رابط_السوبابيس_هنا"
)
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY",
    "مفتاح_السوبابيس_هنا"
)
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
# =========================
# Main Page
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form
        patient_name = data.get("patient_name")
        national_id = data.get("national_id")
        file_number = data.get("file_number")
        patient_phone = data.get("patient_phone")
        requested_service = data.get("requested_service")
        service_name = data.get("service_name")
        employee_name = data.get("employee_name")
        record_date = data.get("record_date")
        record_time = data.get("record_time")
        # حفظ بيانات المريض في Supabase
        record = {
            "patient_name": patient_name,
            "national_id": national_id,
            "file_number": file_number,
            "patient_phone": patient_phone,
            "requested_service": requested_service,
            "service_name": service_name,
            "employee_name": employee_name,
            "record_date": record_date,
            "record_time": record_time
        }
        try:
            supabase \
                .table("patient_records") \
                .insert(record) \
                .execute()
            return redirect(url_for("index"))
        except Exception as e:
            print(
                "Error saving record to Supabase:",
                e
            )
            return jsonify({
                "success": False,
                "message":
                    f"حدث خطأ أثناء حفظ البيانات: {str(e)}"
            }), 500
    # =========================
    # جلب السجلات
    # =========================
    try:
        response = (
            supabase
            .table("patient_records")
            .select("*")
            .execute()
        )
        records = response.data or []
    except Exception as e:
        print(
            "Error fetching records from Supabase:",
            e
        )
        records = []
    return render_template(
        "index.html",
        records=records
    )
# =========================
# Export Excel
# =========================
@app.route("/export-excel", methods=["GET"])
def export_excel():
    return jsonify({
        "success": True,
        "message":
            "تم طلب تصدير السجلات إلى إكسل بنجاح."
    })
# =========================
# حفظ ملاحظات الإجراء
# =========================
@app.route("/save-note", methods=["POST"])
def save_note():
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        action_notes = data.get("action_notes", "").strip()
        # التأكد من وجود رقم السجل
        if not record_id:
            return jsonify({
                "success": False,
                "message":
                    "لم يتم تحديد سجل المريض."
            }), 400
        # التأكد من وجود الملاحظة
        if not action_notes:
            return jsonify({
                "success": False,
                "message":
                    "يرجى كتابة تفاصيل الإجراء المتخذ."
            }), 400
        # تحديث الملاحظة في نفس سجل المريض
        response = (
            supabase
            .table("patient_records")
            .update({
                "action_notes": action_notes
            })
            .eq("id", record_id)
            .execute()
        )
        return jsonify({
            "success": True,
            "message":
                "تم حفظ تفاصيل الإجراء المتخذ بنجاح."
        })
    except Exception as e:
        print(
            "Error saving patient note:",
            e
        )
        return jsonify({
            "success": False,
            "message":
                f"حدث خطأ أثناء حفظ الملاحظة: {str(e)}"
        }), 500
# =========================
# Run App
# =========================
if __name__ == "__main__":
    app.run(debug=True)
