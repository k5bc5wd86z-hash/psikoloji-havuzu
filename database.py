# -*- coding: utf-8 -*-
import os
import sqlite3
from werkzeug.security import generate_password_hash

# Render/Supabase için Postgres kütüphanesini içe aktarmayı dene
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception as e:
    print(f"🔥🔥🔥 GİZLİ HATA YAKALANDI: {e}")
    psycopg2 = None

class DBWrapper:
    """
    Sihirli Köprü Sınıfı:
    app.py veya diğer dosyalardaki SQL kodlarını (fetchone, fetchall vb.) 
    hiç değiştirmeden projenin Supabase (PostgreSQL) ile çalışmasını sağlar.
    """
    def __init__(self, conn, is_postgres=False):
        self.conn = conn
        self.is_postgres = is_postgres

    def execute(self, query, params=()):
        cursor = self.conn.cursor()
        if self.is_postgres:
            # SQLite '?' formatını Postgres '%s' formatına çevirir
            query = query.replace('?', '%s')
            # SQLite AUTOINCREMENT yapısını Postgres SERIAL yapısına çevirir
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    
    if db_url and psycopg2:
        print("🚀 BAŞARILI: Supabase PostgreSQL'e bağlanıldı!")
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return DBWrapper(conn, is_postgres=True)
    else:
        print("⚠️ HATA: Supabase'e bağlanılamadı! Yerel SQLite'a düşüldü.")
        if not db_url:
            print("Sebep: DATABASE_URL Render'da bulunamadı veya yanlış yazıldı.")
        if not psycopg2:
            print("Sebep: psycopg2 kütüphanesi yüklenmemiş (requirements.txt kontrol et).")
            
        conn = sqlite3.connect('psikoloji_havuzu.db')
        conn.row_factory = sqlite3.Row
        return DBWrapper(conn, is_postgres=False)
        
def init_db():
    conn = get_db_connection()
    
    # 1. Admins tablosu
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
    
    # Eksik sütunları otomatik ekleme
    try:
        conn.execute('ALTER TABLE admins ADD COLUMN verification_code TEXT')
    except Exception:
        pass 

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
        username TEXT,
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

    # UZMAN AJANDA VE NOTLAR TABLOSU
    conn.execute('''CREATE TABLE IF NOT EXISTS expert_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expert_username TEXT,
        folder_name TEXT,
        title TEXT,
        content TEXT
    )''')

    # Admins tablosuna tag sütunu ekleme güvenliği
    try:
        conn.execute('ALTER TABLE admins ADD COLUMN tag TEXT DEFAULT "Uzman"')
    except Exception:
        pass

    # Atanan testler tablosu
    conn.execute('''
        CREATE TABLE IF NOT EXISTS assigned_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expert_username TEXT,
            member_username TEXT,
            test_title TEXT,
            test_content TEXT,
            status TEXT DEFAULT 'Bekliyor',
            result TEXT,
            date TEXT
        )
    ''')
    
    # Kurucu Yönetici Garantisi
    yonetici = conn.execute('SELECT * FROM admins WHERE username = "yonetici"').fetchone()
    if not yonetici:
        hashed_pw = generate_password_hash('yonetici123', method='pbkdf2:sha256') 
        conn.execute('INSERT INTO admins (username, password, role, name, email, status) VALUES (?, ?, ?, ?, ?, ?)',
                     ('yonetici', hashed_pw, 'Kurucu Yönetici', 'Sistem Yöneticisi', 'psikolojihavuzu@gmail.com', 'Onaylı'))

    conn.commit()
    conn.close()
