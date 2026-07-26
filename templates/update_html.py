import os

html_content = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Psikoloji ve Bilim Havuzu</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

    <!-- ÜST NAVBAR -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/">🧠 Psikoloji ve Bilim Havuzu</a>
            <div class="ms-auto">
                {% if session_user %}
                    <span class="text-white me-3">Hoş geldin, {{ session_name }} ({{ session_role }})</span>
                    {% if session_role in ['Sistem Yöneticisi', 'Kurucu Yönetici'] %}
                        <a href="/admin_dashboard" class="btn btn-outline-warning btn-sm me-2">Yönetim Paneli</a>
                    {% endif %}
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Çıkış Yap</a>
                {% else %}
                    <button class="btn btn-outline-light btn-sm" data-bs-toggle="modal" data-bs-target="#loginModal">Giriş Yap</button>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container my-4">
        
        <!-- GÜNÜN SÖZÜ VE TAVSİYE -->
        <div class="row mb-4">
            <div class="col-md-8">
                <div class="alert alert-info shadow-sm">
                    <h5 class="alert-heading">💡 Günün Motivasyon Notu</h5>
                    <p class="mb-0">{{ daily_quote }}</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="alert alert-secondary shadow-sm">
                    <h6 class="alert-heading">📖 Öneri (Kitap & Müzik)</h6>
                    <p class="mb-0"><strong>{{ recommendation.book }}</strong> - {{ recommendation.song }}</p>
                </div>
            </div>
        </div>

        <!-- AKADEMİK ALAN FİLTRELEME ÇUBUĞU -->
        <div class="d-flex flex-wrap gap-2 my-3 p-3 bg-white rounded shadow-sm">
            <span class="align-self-center fw-bold me-2">🔍 Alan Filtresi:</span>
            <a href="/" class="btn btn-outline-secondary btn-sm {% if not selected_discipline %}active{% endif %}">Tüm Alanlar</a>
            {% for d in disciplines %}
            <a href="/?discipline={{ d }}" class="btn btn-outline-primary btn-sm {% if selected_discipline == d %}active{% endif %}">{{ d }}</a>
            {% endfor %}
        </div>

        <!-- 📝 MAKALE / YAZI YAZMA FORMU (Yalnızca Yetkililer ve Uzmanlar Görebilir) -->
        {% if session_role in ['Sistem Yöneticisi', 'Kurucu Yönetici', 'Uzman'] %}
        <div class="card my-4 p-4 shadow-sm border-0 bg-white">
            <h4 class="text-primary mb-3">✍️ Yeni Akademik Makale / Yazı Yayınla</h4>
            <form action="/add_post" method="POST">
                <div class="mb-3">
                    <label class="form-label">Makale Başlığı</label>
                    <input type="text" name="title" class="form-control" required placeholder="Araştırma başlığını girin...">
                </div>
                <div class="mb-3">
                    <label class="form-label">Akademik Disiplin / Alan</label>
                    <select name="discipline" class="form-select">
                        {% for d in disciplines %}
                        <option value="{{ d }}">{{ d }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label">Makale İçeriği</label>
                    <textarea name="content" class="form-control" rows="5" required placeholder="Bilimsel metninizi veya makalenizi buraya yazın..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Yayınla</button>
            </form>
        </div>
        {% endif %}

        <!-- MAKALE AKIŞI LİSTESİ -->
        <div class="row">
            <div class="col-md-8">
                <h3 class="mb-3">📚 Bilimsel Makaleler ve Araştırmalar</h3>
                {% if posts %}
                    {% for post in posts %}
                    <div class="card mb-3 shadow-sm border-0">
                        <div class="card-body">
                            <h4 class="card-title text-dark">{{ post.title }}</h4>
                            <h6 class="card-subtitle mb-2 text-muted">Disiplin: {{ post.discipline }} | Yazar: {{ post.author }}</h6>
                            <p class="card-text mt-3" style="white-space: pre-line;">{{ post.content }}</p>
                            
                            <div class="d-flex justify-content-between align-items-center mt-3">
                                <a href="/like_post/{{ post.id }}" class="btn btn-outline-danger btn-sm">
                                    ❤️ Beğen (<span class="badge bg-danger">{{ post.likes }}</span>)
                                </a>
                                
                                {% if session_role in ['Sistem Yöneticisi', 'Kurucu Yönetici', 'Uzman'] %}
                                <a href="/delete_post/{{ post.id }}" class="btn btn-outline-dark btn-sm" onclick="return confirm('Bu makaleyi silmek istediğinize emin misiniz?');">Sil</a>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="alert alert-warning">Bu alanda henüz yayınlanmış bir makale bulunmuyor.</div>
                {% endif %}
            </div>

            <!-- SAĞ TARAF: UZMANLAR VE ORTAK ÇALIŞMA CHAT ALANI -->
            <div class="col-md-4">
                <!-- ONAYLI UZMANLAR LİSTESİ -->
                <div class="card shadow-sm mb-4 border-0">
                    <div class="card-header bg-primary text-white">
                        <h5 class="mb-0">👨‍⚕️ Onaylı Uzmanlar</h5>
                    </div>
                    <ul class="list-group list-group-flush">
                        {% for exp in experts %}
                        <li class="list-group-item">
                            <strong>{{ exp.name }}</strong> <br><small class="text-muted">{{ exp.role }}</small>
                        </li>
                        {% else %}
                        <li class="list-group-item text-muted">Henüz onaylı uzman bulunmuyor.</li>
                        {% endfor %}
                    </ul>
                </div>

                <!-- 💬 ORTAK ÇALIŞMA VE DESTEK DUVARI (CHAT) -->
                <div id="destek-duvari" class="card shadow-sm border-0">
                    <div class="card-header bg-dark text-white">
                        <h5 class="mb-0">🤝 Ortak Çalışma & Destek Duvarı</h5>
                    </div>
                    <div class="card-body" style="max-height: 350px; overflow-y: auto;">
                        {% for chat in community_chats %}
                        <div class="mb-2 border-bottom pb-2">
                            <strong>{{ chat.name }}</strong> <small class="text-muted">({{ chat.time }})</small>
                            <p class="mb-1" style="font-size: 14px;">{{ chat.message }}</p>
                        </div>
                        {% else %}
                        <p class="text-muted text-center">Henüz mesaj yazılmamış. İlk mesajı sen yaz!</p>
                        {% endfor %}
                    </div>
                    <div class="card-footer bg-white">
                        <form action="/add_community_chat" method="POST" class="input-group">
                            <input type="text" name="chatMsg" class="form-control" placeholder="Ortak çalışma alanı mesajı..." required>
                            <button class="btn btn-success" type="submit">Gönder</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <!-- GİRİŞ MODALI -->
    <div class="modal fade" id="loginModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <form action="/login" method="POST">
                    <div class="modal-header">
                        <h5 class="modal-title">Sisteme Giriş Yap</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">Kullanıcı Adı</label>
                            <input type="text" name="adminUsername" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Şifre</label>
                            <input type="password" name="adminPassword" class="form-control" required>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="submit" class="btn btn-primary">Giriş Yap</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

os.makedirs('templates', exist_ok=True)
with open('templates/psikoloji_havuzu.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ HTML şablonu 'templates/psikoloji_havuzu.html' konumuna kusursuzca kaydedildi!")
