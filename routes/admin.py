# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, session
import os
from database import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']: 
        return redirect('/')
    
    conn = get_db_connection()
    all_members = []
    pending_experts = []
    
    try:
        all_members = conn.execute('SELECT * FROM members').fetchall()
        pending_experts = conn.execute("SELECT * FROM admins WHERE status LIKE '%Bekliyor%'").fetchall()
    except Exception as e:
        print("Admin dashboard veri çekme hatası:", e)
    finally:
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
    admin_user = os.environ.get('ADMIN_USERNAME', 'yonetici')
    experts = conn.execute('SELECT * FROM admins WHERE username != ?', (admin_user,)).fetchall()
    conn.close()
    return render_template('admin_settings.html', settings=settings, experts=experts)

@admin_bp.route('/admin/update_settings', methods=['POST'])
def admin_update_settings():
    if session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        return redirect('/')
    
    brand_name = request.form.get('brand_name')
    hero_title = request.form.get('hero_title')
    hero_subtitle = request.form.get('hero_subtitle')
    
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM site_settings WHERE id = 1').fetchone()
    
    if settings:
        conn.execute('UPDATE site_settings SET brand_name = ?, hero_title = ?, hero_subtitle = ? WHERE id = 1',
                     (brand_name, hero_title, hero_subtitle))
    else:
        conn.execute('INSERT INTO site_settings (brand_name, hero_title, hero_subtitle) VALUES (?, ?, ?)',
                     (brand_name, hero_title, hero_subtitle))
    
    conn.commit()
    conn.close()
    return redirect('/admin/settings')

@admin_bp.route('/update_expert_tag/<int:expert_id>', methods=['POST'])
def update_expert_tag(expert_id):
    if not session.get('user') or session.get('role') not in ['Sistem Yöneticisi', 'Kurucu Yönetici']:
        return redirect(url_for('anasayfa'))
        
    new_tag = request.form.get('expertTag', 'Uzman')
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE admins SET tag = ? WHERE id = ?', (new_tag, expert_id))
        conn.commit()
    except Exception:
        if 'conn' in locals() and conn is not None:
            try:
                if getattr(conn, 'is_postgres', False):
                    conn.conn.rollback()
            except Exception:
                pass
        raise
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()
            
    return redirect(url_for('anasayfa'))
