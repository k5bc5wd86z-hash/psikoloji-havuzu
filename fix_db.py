import sqlite3

conn = sqlite3.connect('psikoloji_havuzu.db')
conn.execute('ALTER TABLE posts ADD COLUMN username TEXT;')
conn.commit()
conn.close()
print("Veritabanı başarıyla güncellendi, eksik sütun eklendi!")
