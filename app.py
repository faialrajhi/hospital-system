from flask import Flask, render_template, request, send_file, redirect, url_for
from supabase import create_client, Client
import pandas as pd
import io
import os

app = Flask(__name__)

# إعدادات الاتصال بـ Supabase (تأكدِ أن المتغيرات معرفة أو ضعي الروابط مباشرة هنا)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "رابط_سูปابيز_حقك")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "مفتاح_سูปابيز_حقك")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    # الصفحة الرئيسية اللي فيها نموذج (Form) اختيار التواريخ
    return render_template('index.html')

@app.route('/filter_data', methods=['POST'])
def filter_data():
    # 1. استقبال التواريخ المحددة من النموذج
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    try:
        # 2. استعلام البيانات من Supabase حسب التواريخ المحددة
        # ملاحظة: استبدلي 'your_table_name' باسم جدولك، و 'created_at' باسم عمود التاريخ عندك
        response = supabase.table('your_table_name') \
            .select("*") \
            .gte('created_at', start_date) \
            .lte('created_at', end_date) \
            .execute()
        
        data = response.data
    except Exception as e:
        data = []
        print(f"Error fetching data: {e}")

    # 3. تمرير البيانات لصفحة المعاينة HTML لعرضها بجدول
    return render_template('preview_data.html', data=data, start_date=start_date, end_date=end_date)

@app.route('/download_excel', methods=['POST'])
def download_excel():
    # 4. مسار تحميل ملف Excel بناءً على نفس التواريخ المعتمدة
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    try:
        response = supabase.table('your_table_name') \
            .select("*") \
            .gte('created_at', start_date) \
            .lte('created_at', end_date) \
            .execute()
        
        data = response.data
        
        if data:
            # تحويل البيانات إلى Pandas DataFrame ثم إلى ملف Excel
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Filtered Data')
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'report_{start_date}to{end_date}.xlsx'
            )
    except Exception as e:
        print(f"Error exporting excel: {e}")
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
