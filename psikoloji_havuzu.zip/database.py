# -*- coding: utf-8 -*-
import sqlite3
from werkzeug.security import generate_password_hash

def get_db_connection():
    conn = sqlite3.connect('psikoloji_havuzu.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. Yöneticiler ve Uzmanlar
    conn.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        cv TEXT,
        photo TEXT,
        status TEXT
    )''')
    
    # 2. Standart Üyeler
    conn.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        gender TEXT,
        last_period TEXT
    )''')
    
    # 3. Makaleler (Güncel Sütunlarla)
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        category TEXT,
        author TEXT,
        likes INTEGER
    )''')
    
    # 4. Uzman Ortak Çalışma Odası
    conn.execute('''CREATE TABLE IF NOT EXISTS expert_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        sender TEXT,
        message TEXT,
        time TEXT
    )''')

    # 5. Topluluk Destek Duvarı
    conn.execute('''CREATE TABLE IF NOT EXISTS community_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        name TEXT,
        message TEXT,
        time TEXT
    )''')

    # 6. Randevular
    conn.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expert_username TEXT,
        user_name TEXT,
        date TEXT,
        time TEXT,
        reason TEXT,
        status TEXT
    )''')
    
    # 7. Günlükler
    conn.execute('''CREATE TABLE IF NOT EXISTS diaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        content TEXT,
        date TEXT,
        ai_analysis TEXT
    )''')
    
    # 8. Site Ayarları (Güncel Sütunlarla)
    conn.execute('''CREATE TABLE IF NOT EXISTS site_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT,
        hero_title TEXT,
        hero_subtitle TEXT,
        layout_order TEXT,
        bg_base TEXT,
        bg_card TEXT,
        accent_warm TEXT
    )''')

    # KURUCU YÖNETİCİ HESABINI OTOMATİK OLUŞTUR (Silinmelere Karşı Koruma)
    yonetici = conn.execute('SELECT * FROM admins WHERE username = "yonetici"').fetchone()
    if not yonetici:
        # Şifre otomatik olarak '123456' olarak belirlendi (İstersen sonradan değiştirebilirsin)
        hashed_pw = generate_password_hash('123456', method='pbkdf2:sha256') 
        conn.execute('INSERT INTO admins (username, password, role, name, email, status) VALUES (?, ?, ?, ?, ?, ?)',
                     ('yonetici', hashed_pw, 'Kurucu Yönetici', 'Kurucu', 'admin@psikolojihavuzu.com', 'Onaylı'))

    conn.commit()
    conn.close()