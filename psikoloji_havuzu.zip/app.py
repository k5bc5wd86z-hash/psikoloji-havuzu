# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session
import datetime
import random
from database import get_db_connection, init_db

# Blueprint modüllerimizi dahil ediyoruz
from routes.auth import auth_bp
from routes.expert import expert_bp
from routes.admin import admin_bp

from kutuphane import BOOKS, SONGS

app = Flask(__name__)
app.secret_key = 'psikoloji_havuzu_guvenli_anahtar_2026'

MOTIVATIONAL_QUOTES = [
    "Kendinize karşı nazik olun; zihinsel iyileşme bir yarış değil, bir yolculuktur.",
    "Geçmişi değiştiremezsiniz ama bugünkü farkındalığınızla geleceği yeniden yazabilirsiniz."
]

ACADEMIC_DISCIPLINES = [
    "Klinik Psikoloji & Terapi",
    "Kadın Sağlığı & Psikoloji",
    "Nöropsikoloji & Zihin",
    "Bilişsel Nörobilim",
    "Sosyal Psikoloji",
    "Gelişim Psikolojisi",
    "Psikofarmakoloji"
]

init_db()

# Blueprint'leri ana uygulamaya kaydediyoruz
app.register_blueprint(auth_bp)
app.register_blueprint(expert_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def anasayfa():
    conn = get_db_connection()
    selected_discipline = request.args.get('discipline')
    if selected_discipline:
        posts = conn.execute('SELECT * FROM posts WHERE category = ? ORDER BY id DESC', (selected_discipline,)).fetchall()
    else:
        posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
        
    experts = conn.execute('SELECT * FROM admins WHERE username != "yonetici" AND status="Onaylı"').fetchall()
    settings = conn.execute('SELECT * FROM site_settings WHERE id = 1').fetchone()
    community_chats = conn.execute('SELECT * FROM community_chats ORDER BY id DESC LIMIT 20').fetchall()
    expert_chats = conn.execute('SELECT * FROM expert_chats ORDER BY id DESC LIMIT 20').fetchall()
    appointments = conn.execute('SELECT * FROM appointments ORDER BY id DESC').fetchall()
    diaries = []
    
    daily_quote = random.choice(MOTIVATIONAL_QUOTES)
    
    bugunun_tarihi_str = datetime.date.today().strftime('%Y%m%d')
    gunluk_secici = random.Random(bugunun_tarihi_str)
    
    secilen_kitap = gunluk_secici.choice(BOOKS)
    secilen_sarki = gunluk_secici.choice(SONGS)
    
    recommendation = {
        "book": secilen_kitap["book"],
        "book_author": secilen_kitap["book_author"],
        "song": secilen_sarki["song"],
        "song_desc": secilen_sarki["song_desc"]
    }
    
    is_member = session.get('is_member', False)
    session_user = session.get('user')
    session_name = session.get('name')
    session_role = session.get('role')
    
    if is_member and session_user:
        diaries = conn.execute('SELECT * FROM diaries WHERE username = ? ORDER BY id DESC', (session_user,)).fetchall()
        
    conn.close()
    
    return render_template('psikoloji_havuzu.html', 
                           posts=posts, 
                           experts=experts, 
                           community_chats=community_chats, 
                           expert_chats=expert_chats,
                           appointments=appointments,
                           diaries=diaries,
                           settings=settings, 
                           session_user=session_user, 
                           session_role=session_role, 
                           session_name=session_name, 
                           is_member=is_member, 
                           daily_quote=daily_quote, 
                           recommendation=recommendation,
                           disciplines=ACADEMIC_DISCIPLINES,
                           selected_discipline=selected_discipline)

@app.route('/like_post/<int:post_id>')
def like_post(post_id):
    conn = get_db_connection()
    conn.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('anasayfa'))

@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    if session.get('role') in ['Sistem Yöneticisi', 'Kurucu Yönetici', 'Uzman']:
        conn = get_db_connection()
        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
    return redirect(url_for('anasayfa'))

@app.route('/add_community_chat', methods=['POST'])
def add_community_chat():
    msg = request.form.get('chatMsg')
    if msg:
        name = session.get('name') or session.get('user') or 'Anonim'
        username = session.get('user') or 'ziyaretci'
        conn = get_db_connection()
        conn.execute('INSERT INTO community_chats (username, name, message, time) VALUES (?, ?, ?, ?)', 
                     (username, name, msg, datetime.datetime.now().strftime("%H:%M")))
        conn.commit()
        conn.close()
    return redirect(url_for('anasayfa') + '#destek-duvari')

if __name__ == '__main__':
    app.run(debug=True)