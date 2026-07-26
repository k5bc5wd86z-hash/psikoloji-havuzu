from flask import Blueprint, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from pypdf import PdfReader
import os
import datetime
import re
from database import get_db_connection

expert_bp = Blueprint('expert', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@expert_bp.route('/upload_cv', methods=['POST'])
def upload_cv():
    if session.get('role') == 'Standart Üye' or not session.get('user'):
        return redirect('/')
    
    # Kullanıcının formdan yazdığı detaylı eğitim/sertifika bilgisini alıyoruz
    education_details = request.form.get('educationDetails', 'Eğitim ve kariyer detayları sisteme işlendi.')
    
    if 'cvFile' in request.files:
        file = request.files['cvFile']
        if file and file.filename != '':
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(f"{session.get('user')}_cv.pdf")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
    
    conn = get_db_connection()
    conn.execute('UPDATE admins SET cv = ? WHERE username = ?', (education_details, session.get('user')))
    conn.commit()
    conn.close()
        
    return redirect(url_for('anasayfa'))

@expert_bp.route('/apply_expert', methods=['POST'])
def apply_expert():
    conn = get_db_connection()
    try:
        education_details = request.form.get('expEducation', 'Mezuniyet ve sertifika bilgileri inceleniyor.')
        
        if 'expCvFile' in request.files:
            file = request.files['expCvFile']
            if file and file.filename != '':
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                username_val = request.form.get('expUser', 'aday')
                filename = secure_filename(f"{username_val}_cv.pdf")
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)

        conn.execute('INSERT INTO admins (username, password, role, name, email, cv, photo, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                     (request.form.get('expUser'), 
                      request.form.get('expPass'), 
                      request.form.get('expRole'), 
                      request.form.get('expName'), 
                      request.form.get('expEmail'), 
                      education_details, '👤', 'Çevrimiçi Görüşme Bekliyor'))
        conn.commit()
    except Exception as e: 
        print("Uzman başvuru hatası:", e)
    finally:
        conn.close()
    return redirect(url_for('anasayfa'))

@expert_bp.route('/add_post', methods=['POST'])
def add_post():
    title = request.form.get('postTitle') or request.form.get('title')
    raw_content = request.form.get('postContent') or request.form.get('content')
    category = request.form.get('postCategory') or request.form.get('discipline', 'Klinik Psikoloji & Terapi')
    
    author_name = session.get('name') or session.get('user') or 'Anonim Uzman'
    author_role = session.get('role') or 'Yazar'
    bugunun_tarihi = datetime.date.today().strftime("%d.%m.%Y")
    
    formatted_content = f"{raw_content}\n\n──────────────\n✒️ Yazar: {author_name} ({author_role})\n📅 Tarih: {bugunun_tarihi}"
    
    if title and raw_content:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO posts (title, content, category, author, likes) VALUES (?, ?, ?, ?, ?)', 
                         (title, formatted_content, category, author_name, 0))
        except Exception as e:
            print("Veritabanı makale ekleme hatası:", e)
            conn.execute('INSERT INTO posts (title, content, likes) VALUES (?, ?, ?)', (title, formatted_content, 0))
        conn.commit()
        conn.close()
    return redirect(url_for('anasayfa'))