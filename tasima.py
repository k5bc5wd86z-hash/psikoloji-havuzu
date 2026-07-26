# -*- coding: utf-8 -*-
from database import get_db_connection, init_db
from kutuphane import BOOKS, SONGS

# Önce tabloların olduğundan emin olalım
init_db()

conn = get_db_connection()

print("Kitaplar veritabanına aktarılıyor...")
for kitap in BOOKS:
    # Aynı kitabın iki kere eklenmesini önlemek için basit bir kontrol
    mevcut = conn.execute('SELECT id FROM books WHERE book = ?', (kitap['book'],)).fetchone()
    if not mevcut:
        conn.execute('INSERT INTO books (book, book_author) VALUES (?, ?)', 
                     (kitap['book'], kitap['book_author']))

print("Şarkılar veritabanına aktarılıyor...")
for sarki in SONGS:
    mevcut = conn.execute('SELECT id FROM songs WHERE song = ?', (sarki['song'],)).fetchone()
    if not mevcut:
        conn.execute('INSERT INTO songs (song, song_desc) VALUES (?, ?)', 
                     (sarki['song'], sarki['song_desc']))

conn.commit()
conn.close()
print("Aktarım başarıyla tamamlandı! Artık kutuphane.py dosyasını silebilirsin.")