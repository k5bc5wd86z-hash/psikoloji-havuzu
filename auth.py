# -*- coding: utf-8 -*-
import random
import resend
from flask import Blueprint, request, redirect, url_for, session, render_template, flash
from database import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('adminUsername') or request.form.get('username')
    password = request.form.get('adminPassword') or request.form.get('password')
    
    conn = get_db_connection()
    
    # 1. Kurucu Yönetici
    if username == 'yonetici':
        admin = conn.execute('SELECT * FROM admins WHERE username = "yonetici"').fetchone()
        
        if admin and check_password_hash(admin['password'], password):
            code = str(random.randint(100000, 999999))
            conn.execute('UPDATE admins SET verification_code = ? WHERE id = ?', (code, admin['id']))
            conn.commit()
            conn.close()
            
            try:
                resend.Emails.send({
                    "from": "Psikoloji Havuzu <iletisim@psikolojihavuzu.com>",
                    "to": ["sunayssssila@gmail.com"],
                    "subject": "Psikoloji Havuzu - Yönetici Giriş Doğrulama Kodu",
                    "html": f"<p>Merhaba {admin['name']},</p><p>Yönetici paneline giriş yapmak için onay kodunuz:</p><h2>{code}</h2><p>Bu kodu talep etmediyseniz lütfen dikkate almayın.</p>"
                })
            except Exception as e:
                print("2FA mail gönderim hatası:", e)
                
            session['pending_user_id'] = admin['id']
            return redirect(url_for('auth.verify_code_page'))
            
        conn.close()
        return redirect(url_for('anasayfa'))
    
    # 2. Uzman Girişi
    expert = conn.execute('SELECT * FROM admins WHERE username = ?', (username,)).fetchone()
    if expert and check_password_hash(expert['password'], password):
        if expert['status'] != 'Onaylı':
            conn.close()
            return "Hesabınız henüz onaylanmamış.", 403
        session['user'] = expert['username']
        session['role'] = expert['role']
        session['name'] = expert['name']
        session['is_member'] = False
        conn.close()
        return redirect(url_for('anasayfa'))
        
    # 3. Standart Üye Girişi
    member = conn.execute('SELECT * FROM members WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if member and check_password_hash(member['password'], password):
        session['user'] = member['username']
        session['role'] = 'Standart Üye'
        session['name'] = member['name']
        session['is_member'] = True
        return redirect(url_for('anasayfa'))
        
    return redirect(url_for('anasayfa'))

@auth_bp.route('/verify_code', methods=['GET', 'POST'])
def verify_code_page():
    if request.method == 'POST':
        entered_code = request.form.get('verificationCode')
        user_id = session.get('pending_user_id')
        
        if user_id:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM admins WHERE id = ?', (user_id,)).fetchone()
            
            if user and user['verification_code'] == entered_code:
                session['user'] = user['username']
                session['role'] = user['role']
                session['name'] = user['name']
                session['is_member'] = False
                
                conn.execute('UPDATE admins SET verification_code = NULL WHERE id = ?', (user_id,))
                conn.commit()
                conn.close()
                
                session.pop('pending_user_id', None)
                return redirect('/admin_dashboard')
            else:
                conn.close()
                flash('Hatalı veya geçersiz kod.', 'danger')
                
    return render_template('verify_code.html')

@auth_bp.route('/register_member', methods=['POST'])
def register_member():
    username = request.form.get('regUsername')
    raw_password = request.form.get('regPassword')
    name = request.form.get('regName')
    gender = request.form.get('regGender')
    
    if not username or not raw_password:
        return redirect(url_for('anasayfa'))

    hashed_password = generate_password_hash(raw_password, method='pbkdf2:sha256')
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO members (username, password, name, gender) VALUES (?, ?, ?, ?)', 
                     (username, hashed_password, name, gender))
        conn.commit()
    except Exception as e:
        print("SQL KAYIT HATASI:", e)
    finally:
        conn.close()
        
    return redirect(url_for('anasayfa'))

@auth_bp.route('/logout')
def logout(): 
    session.clear() 
    return redirect(url_for('anasayfa'))