import os
import cv2
import json
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
from model_loader import detect_bicycles

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

HISTORY_FILE = 'history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(filename, count, result_path):
    history = load_history()
    history.append({
        'timestamp': datetime.now().isoformat(),
        'filename': filename,
        'count': count,
        'result_path': result_path
    })
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(upload_path)

    result_img, count = detect_bicycles(upload_path)

    result_filename = f"res_{file.filename}"
    result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    cv2.imwrite(result_path, result_img)

    save_history(file.filename, count, result_path)

    return jsonify({
        'count': count,
        'result_url': f'/static/results/{result_filename}'
    })

# ------ PDF-отчёт (новая версия) ------
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

@app.route('/report/pdf')
def generate_pdf():
    history = load_history()[-10:]
    pdf_path = 'reports/report.pdf'
    os.makedirs('reports', exist_ok=True)
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Отчёт по учёту велосипедов")
    y -= 30
    c.setFont("Helvetica", 12)

    for record in history:
        if y < 150:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 12)
        line = f"{record['timestamp']}   {record['filename']}   Велосипедов: {record['count']}"
        c.drawString(50, y, line)
        y -= 20
        result_path = record['result_path']
        if os.path.exists(result_path):
            img = ImageReader(result_path)
            c.drawImage(img, 50, y-80, width=150, height=100, preserveAspectRatio=True)
            y -= 110
        else:
            y -= 20
        y -= 20
    c.save()
    return send_file(pdf_path, as_attachment=True)

# ------ Excel-отчёт (опционально) ------
from openpyxl import Workbook

@app.route('/report/excel')
def generate_excel():
    history = load_history()
    wb = Workbook()
    ws = wb.active
    ws.title = "История"
    ws.append(["Время", "Файл", "Количество велосипедов"])
    for rec in history:
        ws.append([rec['timestamp'], rec['filename'], rec['count']])
    excel_path = 'reports/history.xlsx'
    wb.save(excel_path)
    return send_file(excel_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)