# -*- coding: utf-8 -*-
import sqlite3
from werkzeug.security import generate_password_hash

def get_db_connection():
    conn = sqlite3.connect('psikoloji_havuzu.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Tüm tablolar eksiksiz
    conn.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        cv TEXT,
        photo TEXT,
        status TEXT,
        verification_code TEXT
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        gender TEXT,
        last_period TEXT
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        category TEXT,
        author TEXT,
        likes INTEGER DEFAULT 0,
        date_posted TEXT
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        date_posted TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        referring_expert TEXT NOT NULL,
        receiving_expert TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'Beklemede',
        date_referred TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS site_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_name TEXT,
        hero_title TEXT,
        hero_subtitle TEXT,
        layout_order TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expert_username TEXT,
        user_name TEXT,
        date TEXT,
        time TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Bekliyor'
    )''')

    # --- EKSİK OLAN DİĞER TABLOLAR EKLENDİ ---
    conn.execute('''CREATE TABLE IF NOT EXISTS expert_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        name TEXT,
        message TEXT,
        time TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS community_chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        name TEXT,
        message TEXT,
        time TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS diaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        content TEXT,
        date TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book TEXT,
        book_author TEXT
    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        song TEXT,
        song_desc TEXT
    )''')

    # Kurucu Yönetici Garantisi (Kullanıcı: yonetici, Şifre: yonetici123)
    yonetici = conn.execute('SELECT * FROM admins WHERE username = "yonetici"').fetchone()
    if not yonetici:
        hashed_pw = generate_password_hash('yonetici123', method='pbkdf2:sha256') 
        conn.execute('INSERT INTO admins (username, password, role, name, email, status) VALUES (?, ?, ?, ?, ?, ?)',
                     ('yonetici', hashed_pw, 'Kurucu Yönetici', 'Sistem Yöneticisi', 'psikolojihavuzu@gmail.com', 'Onaylı'))

    conn.commit()
    conn.close()