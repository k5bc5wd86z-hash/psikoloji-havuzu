from flask import Blueprint, request, redirect, url_for, session
from database import get_db_connection
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('adminUsername')
    password = request.form.get('adminPassword')
    
    conn = get_db_connection()
    
    # 1. Kurucu Yönetici Girişi
    if username == 'yonetici':
        admin = conn.execute('SELECT * FROM admins WHERE username = "yonetici"').fetchone()
        conn.close()
        if admin and check_password_hash(admin['password'], password):
            session['user'] = 'yonetici'
            session['role'] = 'Sistem Yöneticisi'
            session['name'] = 'Yönetici'
            session['is_member'] = False
            return redirect('/admin_dashboard')
        return redirect(url_for('anasayfa'))
    
    # 2. Uzman Girişi
    expert = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password)).fetchone()
    if expert:
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
    member = conn.execute('SELECT * FROM members WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    if member:
        session['user'] = member['username']
        session['role'] = 'Standart Üye'
        session['name'] = member['name']
        session['is_member'] = True
        
    return redirect(url_for('anasayfa'))

@auth_bp.route('/register_member', methods=['POST'])
def register_member():
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO members (username, password, name, gender) VALUES (?, ?, ?, ?)', 
                     (request.form.get('regUsername'), request.form.get('regPassword'), request.form.get('regName'), request.form.get('regGender')))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect(url_for('anasayfa'))

@auth_bp.route('/logout')
def logout(): 
    session.clear() 
    return redirect(url_for('anasayfa'))