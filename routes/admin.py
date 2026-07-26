from flask import Blueprint, render_template, request, redirect, jsonify, session
from database import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']: 
        return redirect('/')
    conn = get_db_connection()
    all_members = conn.execute('SELECT * FROM members').fetchall()
    pending_experts = conn.execute('SELECT * FROM admins WHERE status LIKE "%Bekliyor%"').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', all_members=all_members, pending_experts=pending_experts)

@admin_bp.route('/admin/approve_expert/<username>')
def approve_expert(username):
    if session.get('role') in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        conn = get_db_connection()
        conn.execute('UPDATE admins SET status="Onaylı" WHERE username=?', (username,))
        conn.commit()
        conn.close()
    return redirect('/admin_dashboard')

@admin_bp.route('/admin/reject_expert/<username>')
def reject_expert(username):
    if session.get('role') in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        conn = get_db_connection()
        conn.execute('DELETE FROM admins WHERE username=?', (username,))
        conn.commit()
        conn.close()
    return redirect('/admin_dashboard')

@admin_bp.route('/admin/delete_member/<username>')
def delete_member(username):
    if session.get('role') in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        conn = get_db_connection()
        conn.execute('DELETE FROM members WHERE username=?', (username,))
        conn.commit()
        conn.close()
    return redirect('/admin_dashboard')

@admin_bp.route('/admin/delete_expert/<username>')
def delete_expert(username):
    if session.get('role') in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        conn = get_db_connection()
        conn.execute('DELETE FROM admins WHERE username = ?', (username,))
        conn.commit()
        conn.close()
    return redirect('/admin/settings')

@admin_bp.route('/admin/settings')
def admin_settings():
    if session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        return redirect('/')
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM site_settings WHERE id = 1').fetchone()
    experts = conn.execute('SELECT * FROM admins WHERE username != "yonetici"').fetchall()
    conn.close()
    return render_template('admin_settings.html', settings=settings, experts=experts)

@admin_bp.route('/admin/update_settings', methods=['POST'])
def admin_update_settings():
    if session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        return redirect('/')
    brand_name = request.form.get('brand_name')
    hero_title = request.form.get('hero_title')
    hero_subtitle = request.form.get('hero_subtitle')
    layout_order = request.form.get('layout_order')
    
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM site_settings WHERE id = 1').fetchone()
    if settings:
        conn.execute('UPDATE site_settings SET brand_name = ?, hero_title = ?, hero_subtitle = ?, layout_order = ? WHERE id = 1',
                     (brand_name, hero_title, hero_subtitle, layout_order))
    else:
        conn.execute('INSERT INTO site_settings (brand_name, hero_title, hero_subtitle, layout_order) VALUES (?, ?, ?, ?)',
                     (brand_name, hero_title, hero_subtitle, layout_order))
    conn.commit()
    conn.close()
    return redirect('/admin/settings')

@admin_bp.route('/admin/execute_terminal', methods=['POST'])
def execute_terminal():
    if session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        return jsonify({'status': 'error', 'message': 'Yetkisiz erişim!'}), 403
    
    code = request.form.get('terminal_code')
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        return jsonify({'status': 'success', 'output': 'Kod başarıyla çalıştırıldı ve dosyalara işlendi!'})
    except Exception as e:
        return jsonify({'status': 'error', 'output': str(e)}), 400