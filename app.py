from flask import Flask, render_template, request, jsonify, redirect, url_for
import os

app = Flask(__name__)

# قائمة أو تخزين مؤقت للسجلات (يمكنك استبدالها بقاعدة بياناتك الحالية)
records = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # استقبال البيانات الواردة من النموذج
        patient_name = request.form.get('patient_name')
        national_id = request.form.get('national_id')
        file_number = request.form.get('file_number')
        patient_phone = request.form.get('patient_phone')
        requested_service = request.form.get('requested_service')
        service_name = request.form.get('service_name')
        employee_name = request.form.get('employee_name')
        record_date = request.form.get('record_date')
        record_time = request.form.get('record_time')
        
        # إنشاء قاموس السجل الجديد
        new_record = {
            'patient_name': patient_name,
            'national_id': national_id,
            'file_number': file_number,
            'patient_phone': patient_phone,
            'requested_service': requested_service,
            'service_name': service_name,
            'employee_name': employee_name,
            'record_date': record_date,
            'record_time': record_time
        }
        
        # إضافة السجل إلى القائمة
        records.append(new_record)
        return redirect(url_for('index'))
        
    return render_template('index.html', records=records)

@app.route('/export-excel')
def export_excel():
    # مسار تصدير الإكسل (يمكنك تعديله حسب طريقتك الحالية)
    return "تم طلب تصدير السجلات إلى إكسل بنجاح."

# مسار استقبال طلبات الـ SMS لتجنب ظهور خطأ في الاتصال
@app.route('/send-sms', methods=['POST'])
def send_sms():
    data = request.get_json()
    phone = data.get('phone')
    name = data.get('name')
    ticket = data.get('ticket')
    service = data.get('service')
    
    # يمكنك ربط بوابة رسائل حقيقية هنا لاحقاً
    return jsonify({
        'success': False, 
        'message': 'خدمة مزود الرسائل النصية غير مجهزة برمجياً بعد في السيرفر.'
    })

if __name__ == '__main__':
    app.run(debug=True)
