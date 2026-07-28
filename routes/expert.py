# -*- coding: utf-8 -*-
import os
import datetime
import resend
from flask import Blueprint, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
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
        raw_password = request.form.get('expPass')
        hashed_password = generate_password_hash(raw_password, method='pbkdf2:sha256') if raw_password else None
        
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
                      hashed_password, 
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
@expert_bp.route('/add_post', methods=['POST'])
@expert_bp.route('/publish_article', methods=['POST'])
def add_post():
    title = request.form.get('postTitle') or request.form.get('title')
    raw_content = request.form.get('postContent') or request.form.get('content')
    category = request.form.get('postCategory') or request.form.get('category') or request.form.get('discipline', 'Klinik Psikoloji & Terapi')
    
    author_name = session.get('name') or session.get('user') or 'Anonim Uzman'
    bugunun_tarihi = datetime.date.today().strftime("%d.%m.%Y")
    
    formatted_content = f"{raw_content}\n\n──────────────\nTarih: {bugunun_tarihi}"
    
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
    
@expert_bp.route('/refer_client', methods=['POST'])
def refer_client():
    if session.get('role') == 'Standart Üye' or not session.get('user'):
        return redirect('/')
        
    client_name = request.form.get('clientName')
    target_expert = request.form.get('targetExpert')
    referral_note = request.form.get('referralNote')
    
    if client_name and target_expert and referral_note:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO referrals (client_name, referring_expert, receiving_expert, reason) VALUES (?, ?, ?, ?)',
                         (client_name, session.get('user'), target_expert, referral_note))
            conn.commit()
        except Exception as e:
            print("Yönlendirme hatası:", e)
        finally:
            conn.close()
            
    return redirect(url_for('anasayfa'))

@expert_bp.route('/add_appointment', methods=['POST'])
def add_appointment():
    expert_username = request.form.get('apptExpertUsername')
    user_name = request.form.get('apptUserName')
    date = request.form.get('apptDate')
    time = request.form.get('apptTime')
    reason = request.form.get('apptReason')
    
    if expert_username and user_name and date and time:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO appointments (expert_username, user_name, date, time, reason, status)
            VALUES (?, ?, ?, ?, ?, 'Bekliyor')
        ''', (expert_username, user_name, date, time, reason))
        conn.commit()
        
        expert = conn.execute('SELECT email, name FROM admins WHERE username = ?', (expert_username,)).fetchone()
        conn.close()
        
        if expert and expert['email']:
            try:
                resend.Emails.send({
                    "from": "Psikoloji Havuzu <iletisim@psikolojihavuzu.com>",
                    "to": [expert['email'] or "psikolojihavuzu@gmail.com"],
                    "subject": f"Psikoloji Havuzu - Yeni Randevu Talebi: {user_name}",
                    "html": f"<p>Merhaba {expert['name']},</p><p>Sistem üzerinden yeni bir randevu talebi aldınız.</p><ul><li><strong>Danışan:</strong> {user_name}</li><li><strong>Tarih:</strong> {date} | {time}</li><li><strong>Görüşme Nedeni:</strong> {reason}</li></ul><p>Lütfen panelinizden onay veriniz.</p>"
                })
            except Exception as e:
                print("Randevu maili gönderilemedi:", e)
                
    return redirect(url_for('anasayfa'))

@expert_bp.route('/update_appointment/<int:appt_id>/<status>', methods=['POST', 'GET'])
def update_appointment(appt_id, status):
    if status in ['Onaylandı', 'Reddedildi']:
        conn = get_db_connection()
        try:
            conn.execute('UPDATE appointments SET status = ? WHERE id = ?', (status, appt_id))
            conn.commit()
        except Exception as e:
            print("Randevu durum güncelleme hatası:", e)
        finally:
            conn.close()   
            
    return redirect(url_for('anasayfa'))

@expert_bp.route('/edit_post/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    if not session.get('user'):
        return redirect(url_for('anasayfa'))
        
    title = request.form.get('title')
    category = request.form.get('category')
    content = request.form.get('content')
    
    if title and content:
        conn = get_db_connection()
        try:
            conn.execute('''
                UPDATE posts 
                SET title = ?, category = ?, content = ? 
                WHERE id = ?
            ''', (title, category, content, post_id))
            conn.commit()
        except Exception as e:
            print("Makale güncelleme hatası:", e)
        finally:
            conn.close()
            
    return redirect(url_for('anasayfa'))
