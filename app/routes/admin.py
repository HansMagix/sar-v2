from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from app.db import get_users_db
import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Simple Secret Key
ADMIN_KEY = "admin123"

def is_admin():
    # Check session or query param
    # For now, simplistic check
    return request.args.get('key') == ADMIN_KEY

@bp.route('/dashboard')
def dashboard():
    if not is_admin():
        return "Access Denied. Please provide the correct key.", 403
        
    db = get_users_db()
    # Fetch Pending Transactions
    transactions = db.execute('''
        SELECT t.*, s.phone 
        FROM transactions t
        JOIN sessions s ON t.user_uuid = s.uuid
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    return render_template('admin/dashboard.html', transactions=transactions, key=ADMIN_KEY)

@bp.route('/dashboard/rows')
def dashboard_rows():
    if not is_admin():
        return "Access Denied", 403
        
    db = get_users_db()
    transactions = db.execute('''
        SELECT t.*, s.phone 
        FROM transactions t
        JOIN sessions s ON t.user_uuid = s.uuid
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    return render_template('admin/transactions_rows.html', transactions=transactions)

@bp.route('/revoke/<int:transaction_id>', methods=['POST'])
def revoke(transaction_id):
    db = get_users_db()
    
    # 1. Get Transaction
    trx = db.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    if not trx:
        return jsonify({'success': False, 'message': 'Transaction not found'})
    
    user_uuid = trx['user_uuid']
    
    # 2. Update Transaction Status
    db.execute("UPDATE transactions SET status = 'REVOKED' WHERE id = ?", (transaction_id,))
    
    # 3. Downgrade User Session
    db.execute("UPDATE sessions SET tier = 'basic', status = 'PENDING', expiry = NULL WHERE uuid = ?", (user_uuid,))
    
    db.commit()
    return jsonify({'success': True})

@bp.route('/approve/<int:transaction_id>', methods=['POST'])
def approve(transaction_id):
    db = get_users_db()
    
    # 1. Get Transaction
    trx = db.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,)).fetchone()
    if not trx:
        return jsonify({'success': False, 'message': 'Transaction not found'})
        
    user_uuid = trx['user_uuid']
    
    # 2. Update Transaction Status
    db.execute("UPDATE transactions SET status = 'APPROVED' WHERE id = ?", (transaction_id,))
    
    # 3. Upgrade User Session
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    db.execute("UPDATE sessions SET tier = 'premium', status = 'PAID', expiry = ? WHERE uuid = ?", (expiry, user_uuid))
    
    db.commit()
    return jsonify({'success': True})

@bp.route('/reject/<int:transaction_id>', methods=['POST'])
def reject(transaction_id):
    db = get_users_db()
    db.execute("UPDATE transactions SET status = 'REJECTED' WHERE id = ?", (transaction_id,))
    db.commit()
    return jsonify({'success': True})
