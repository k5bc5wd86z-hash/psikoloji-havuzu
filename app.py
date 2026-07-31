# -*- coding: utf-8 -*-
import os
import resend
import datetime
import random
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from database import get_db_connection, init_db
from routes.auth import auth_bp
from routes.expert import expert_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.secret_key = 'psikoloji_havuzu_guvenli_anahtar_2026'

# Resend API Ayarı
resend.api_key = os.environ.get("RESEND_API_KEY")

# Veritabanını başlat
init_db()

# Blueprint Kayıtları
app.register_blueprint(auth_bp)
app.register_blueprint(expert_bp)
app.register_blueprint(admin_bp)

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
    "Psikofarmakoloji",
    "Hasta Hakları"
]

@app.route('/')
def anasayfa():
    conn = get_db_connection()
    user_role = session.get('role')
    session_user = session.get('user')
    
    # 1. KONTROL: Eğer giriş yapan KESİNLİKLE 'Uzman' ise (Yönetici değilse), uzman panelini yükle
    if user_role == 'Uzman' and session_user:
        appointments = conn.execute('SELECT * FROM appointments ORDER BY id DESC').fetchall()
        expert_notes = conn.execute('SELECT * FROM expert_notes WHERE expert_username = ?', (session_user,)).fetchall()
        conn.close()
        
        return render_template('components/expert_panel.html', 
                               appointments=appointments,
                               expert_notes=expert_notes,
                               session_user=session_user,
                               session_name=session.get('name'),
                               session_role=user_role)
    
    # 2. Uzman değilse (Normal Üye, Ziyaretçi veya Yönetici ise) standart ana sayfayı yükle
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    experts = conn.execute('SELECT * FROM admins WHERE role != "Kurucu Yönetici" AND status = "Onaylı"').fetchall()
    appointments = conn.execute('SELECT * FROM appointments ORDER BY id DESC').fetchall()
    expert_chats = conn.execute('SELECT * FROM expert_chats ORDER BY id DESC').fetchall()
    community_chats = conn.execute('SELECT * FROM community_chats ORDER BY id DESC').fetchall()
    settings = conn.execute('SELECT * FROM site_settings ORDER BY id DESC LIMIT 1').fetchone()
    
    expert_notes = []
    if session_user:
        expert_notes = conn.execute('SELECT * FROM expert_notes WHERE expert_username = ?', (session_user,)).fetchall()

    bugunun_tarihi_str = datetime.date.today().strftime('%Y%m%d')
    gunluk_secici = random.Random(bugunun_tarihi_str)
    
    try:
        book_count = conn.execute('SELECT COUNT(*) FROM books').fetchone()[0]
        song_count = conn.execute('SELECT COUNT(*) FROM songs').fetchone()[0]
    except:
        book_count = 0
        song_count = 0
    
    recommendation = {
        "book": "Kütüphane güncelleniyor...",
        "book_author": "-",
        "song": "Kütüphane güncelleniyor...",
        "song_desc": "-"
    }
    
    if book_count > 0 and song_count > 0:
        random_book_index = gunluk_secici.randint(0, book_count - 1)
        random_song_index = gunluk_secici.randint(0, song_count - 1)
        
        secilen_kitap = conn.execute('SELECT * FROM books LIMIT 1 OFFSET ?', (random_book_index,)).fetchone()
        secilen_sarki = conn.execute('SELECT * FROM songs LIMIT 1 OFFSET ?', (random_song_index,)).fetchone()
        
        if secilen_kitap and secilen_sarki:
            recommendation = {
                "book": secilen_kitap["book"],
                "book_author": secilen_kitap["book_author"],
                "song": secilen_sarki["song"],
                "song_desc": secilen_sarki["song_desc"]
            }
    
    is_member = session.get('is_member', False)
    session_name = session.get('name')
    
    diaries = []
    if is_member and session_user:
        diaries = conn.execute('SELECT * FROM diaries WHERE username = ? ORDER BY id DESC', (session_user,)).fetchall()
        
    member_assigned_tests = []
    if is_member and session_user:
        member_assigned_tests = conn.execute(
            'SELECT * FROM assigned_tests WHERE member_username = ? ORDER BY id DESC', 
            (session_user,)
        ).fetchall()

    expert_assigned_tests = []
    if user_role and user_role != 'Standart Üye' and session_user:
        expert_assigned_tests = conn.execute(
            'SELECT * FROM assigned_tests WHERE expert_username = ? ORDER BY id DESC', 
            (session_user,)
        ).fetchall()
        
    conn.close()
    
    daily_quote = gunluk_secici.choice(MOTIVATIONAL_QUOTES)
    selected_discipline = None
    
    return render_template('psikoloji_havuzu.html', 
                           posts=posts, 
                           experts=experts, 
                           community_chats=community_chats, 
                           expert_chats=expert_chats,
                           appointments=appointments,
                           expert_notes=expert_notes,
                           diaries=diaries,
                           member_assigned_tests=member_assigned_tests,
                           expert_assigned_tests=expert_assigned_tests,
                           settings=settings, 
                           session_user=session_user, 
                           session_role=user_role, 
                           session_name=session_name, 
                           is_member=is_member, 
                           daily_quote=daily_quote, 
                           recommendation=recommendation,
                           disciplines=ACADEMIC_DISCIPLINES,
                           selected_discipline=selected_discipline)
    
@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    conn = get_db_connection()
    conn.execute('UPDATE posts SET likes = likes + 1 WHERE id = ?', (post_id,))
    conn.commit()
    post = conn.execute('SELECT likes FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    if post:
        return jsonify({'success': True, 'new_likes': post['likes']})
    return jsonify({'success': False}), 404

@app.route('/add_diary', methods=['POST'])
def add_diary():
    if not session.get('is_member') or not session.get('user'):
        return redirect(url_for('anasayfa'))
        
    title = request.form.get('diaryTitle')
    content = request.form.get('diaryContent')
    username = session.get('user')
    bugunun_tarihi = datetime.date.today().strftime("%d.%m.%Y")
    
    if title and content:
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO diaries (username, title, content, date)
                VALUES (?, ?, ?, ?)
            ''', (username, title, content, bugunun_tarihi))
            conn.commit()
        except Exception as e:
            print("Günlük ekleme hatası:", e)
        finally:
            conn.close()
            
    return redirect(url_for('anasayfa'))

@app.route('/delete_post/<int:post_id>', methods=['POST', 'GET'])
def delete_post(post_id):
    if session.get('role') in ['Sistem Yöneticisi', 'Kurucu Yönetici', 'Uzman']:
        conn = get_db_connection()
        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
        conn.close()
        flash('Makale başarıyla silindi.', 'success')
    else:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        
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

@app.route('/send_contact', methods=['POST'])
def send_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    
    if name and email and message:
        try:
            resend.Emails.send({
                "from": "Psikoloji Havuzu <iletisim@psikolojihavuzu.com>",
                "to": ["sunayssssila@gmail.com"],
                "subject": f"Psikoloji Havuzu - Yeni İletişim: {name}",
                "html": f"<p><strong>Gönderen:</strong> {name}</p><p><strong>E-posta:</strong> {email}</p><p><strong>Mesaj:</strong><br>{message}</p>"
            })
            flash('Mesajınız başarıyla iletildi.', 'success')
        except Exception as e:
            print("Mail gönderme hatası:", e)
            flash('Mesaj gönderilirken sunucu kaynaklı bir hata oluştu.', 'danger')
            
    return redirect(url_for('anasayfa'))

@app.route('/tum_makaleler')
def tum_makaleler():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    is_member = session.get('is_member', False)
    settings = conn.execute('SELECT * FROM site_settings ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return render_template('tum_makaleler.html', posts=posts, is_member=is_member, settings=settings)

@app.route('/tum_uzmanlar')
def tum_uzmanlar():
    conn = get_db_connection()
    experts = conn.execute('SELECT * FROM admins WHERE role != "Kurucu Yönetici" AND status = "Onaylı"').fetchall()
    settings = conn.execute('SELECT * FROM site_settings ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    return render_template('tum_uzmanlar.html', experts=experts, settings=settings)

@app.route('/etik_kurul_testler')
def etik_kurul_testler():
    if session.get('role') == 'Uzman':
        return render_template('testler.html')
        
    flash('Bu modül yalnızca uzmanlar için erişilebilirdir.', 'warning')
    return redirect(url_for('anasayfa'))

@app.route('/psikoloji_nedir')
def psikoloji_nedir():
    return render_template('psikoloji_nedir.html')

@app.route('/tags')
def tags():
    conn = get_db_connection()
    kurucu_uzmanlar = conn.execute('SELECT * FROM admins WHERE tag = "Kurucu Uzman"').fetchall()
    ornek_makaleler = conn.execute('SELECT * FROM posts LIMIT 2').fetchall()
    conn.close()
    return render_template('psikoloji_havuzu.html', experts=kurucu_uzmanlar, posts=ornek_makaleler)

@app.route('/submit_test/<int:test_id>', methods=['POST'])
def submit_test(test_id):
    if not session.get('is_member') or not session.get('user'):
        return redirect(url_for('anasayfa'))
        
    result_text = request.form.get('testResult')
    if result_text:
        conn = get_db_connection()
        conn.execute('''
            UPDATE assigned_tests 
            SET status = 'Tamamlandı', result = ? 
            WHERE id = ? AND member_username = ?
        ''', (result_text, test_id, session.get('user')))
        conn.commit()
        conn.close()
        
    return redirect(url_for('anasayfa'))

@app.route('/sitemap.xml')
def sitemap():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://www.psikolojihavuzu.com/</loc>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    return xml_content, 200, {'Content-Type': 'application/xml'}

@app.route('/robots.txt')
def robots():
    lines = [
        "User-agent: *",
        "Disallow: /admin_dashboard",
        "Disallow: /logout",
        "Allow: /"
    ]
    return "\n".join(lines), 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    app.run(debug=True)
