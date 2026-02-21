from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template, make_response, g
import uuid
import datetime
from app.services.mpesa_service import MpesaService
from app.services.payment_service import PaymentService
from app.db import get_users_db

bp = Blueprint('payments', __name__)

@bp.route('/verify', methods=['POST'])
def verify_payment():
    # Free Tier Pivot: Payments Disabled
    flash("Payments are no longer required. The app is free!", "success")
    return redirect(url_for('main.index'))

# --- STK PUSH (DEPRECATED/COMMENTED OUT FOR LATER) ---
# @bp.route('/pay', methods=['POST'])
# def pay():
#     phone = request.form.get('phone')
#     tier = request.form.get('tier', 'premium') # default to premium
#     
#     # 1. Sanitize Phone
#     try:
#         clean_phone = MpesaService._sanitize_phone(phone)
#     except ValueError as e:
#         flash(str(e), 'error')
#         return redirect(url_for('main.index'))
#     
#     # 2. Use Existing Session (No new UUID)
#     # g.user is guaranteed by auth.py
#     if not g.user:
#         # Should not happen typically unless cookies disabled
#         flash("Session not found. Please refresh.", 'error')
#         return redirect(url_for('main.index'))
#         
#     session_id = g.user['uuid']
#     
#     # 3. Update DB (Upgrade existing session)
#     db = get_users_db()
#     # Reset status to PENDING
#     db.execute('''
#         UPDATE sessions 
#         SET phone = ?, tier = ?, status = 'PENDING', mpesa_ref = NULL
#         WHERE uuid = ?
#     ''', (clean_phone, tier, session_id))
#     db.commit()
#     
#     # 4. Initiate STK Push
#     try:
#         # Amount 1 for testing (User requested KES 1 in prompt previously, though code said 50 before. Stick to 1.)
#         checkout_req_id = MpesaService.initiate_stk_push(clean_phone, 1, 'SARv2')
#         
#         # Update DB with mpesa_ref
#         db.execute("UPDATE sessions SET mpesa_ref = ? WHERE uuid = ?", (checkout_req_id, session_id))
#         db.commit()
#         
#     except Exception as e:
#         flash("Failed to initiate payment. Please try again.", 'error')
#         return redirect(url_for('main.index'))
#     
#     # 5. Redirect (No new cookie needed, auth.py handles user_id)
#     return redirect(url_for('payments.waiting', session_id=session_id))

# @bp.route('/waiting/<session_id>')
# def waiting(session_id):
#     return render_template('waiting.html', session_id=session_id)

# @bp.route('/check_status/<session_id>', methods=['GET'])
# def check_status(session_id):
#     db = get_users_db()
#     row = db.execute("SELECT status FROM sessions WHERE uuid = ?", (session_id,)).fetchone()
#     if row:
#         return jsonify({'status': row['status']})
#     return jsonify({'status': 'UNKNOWN'})

# @bp.route('/mpesa/callback', methods=['POST'])
# def callback():
#     data = request.json
#     # Parse Safaricom payload
#     try:
#         stk_callback = data.get('Body', {}).get('stkCallback', {})
#         merchant_req_id = stk_callback.get('MerchantRequestID')
#         checkout_req_id = stk_callback.get('CheckoutRequestID')
#         result_code = stk_callback.get('ResultCode')
#         
#         db = get_users_db()
#         
#         # Find session by CheckoutRequestID (stored in mpesa_ref)
#         # Note: If we had concurrent requests, this matches the specific transaction
#         row = db.execute("SELECT uuid FROM sessions WHERE mpesa_ref = ?", (checkout_req_id,)).fetchone()
#         
#         if row:
#             session_uuid = row['uuid']
#             if result_code == 0:
#                 # Success
#                 # Expiry = Now + 7 days (or 24h as per other note, but instruction said 7 days? 
#                 # Instruction in Action 2 says "Now + 7 days").
#                 expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
#                 db.execute("UPDATE sessions SET status = 'PAID', expiry = ? WHERE uuid = ?", (expiry, session_uuid))
#             else:
#                 # Failed
#                 db.execute("UPDATE sessions SET status = 'FAILED' WHERE uuid = ?", (session_uuid))
#             
#             db.commit()
#             
#     except Exception as e:
#         print(f"Callback Error: {e}")
#     
#     return jsonify({"result": "ok"})
