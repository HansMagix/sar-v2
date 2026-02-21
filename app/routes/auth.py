from flask import Blueprint, request, make_response, g, session
import uuid
from app.services.auth_service import get_session, create_session

bp = Blueprint('auth', __name__)

@bp.before_app_request
def load_user():
    # Attempt to read UUID from cookie
    user_uuid = request.cookies.get('user_id')
    
    if user_uuid:
        user = get_session(user_uuid)
        if user:
            g.user = user
        else:
            # Cookie exists but DB doesn't have it (maybe DB wipe). Re-create.
            create_session(user_uuid)
            g.user = get_session(user_uuid)
    else:
        g.user = None

@bp.after_app_request
def set_cookie(response):
    # If no user in g, it means they are new or cleared cookies.
    # We assign them a UUID and set the cookie.
    if g.get('user') is None:
        new_uuid = str(uuid.uuid4())
        create_session(new_uuid)
        g.user = get_session(new_uuid) # Set for this context just in case
        
        # Set cookie that lasts 1 year
        response.set_cookie('user_id', new_uuid, max_age=60*60*24*365)
    
    return response

@bp.route('/my-session')
def show_session():
    # Debug route
    if g.user:
        return {
            'uuid': g.user['uuid'],
            'tier': g.user['tier'],
            'status': g.user['status'],
            'expiry': g.user['expiry']
        }
    return {'status': 'creating_session'}

@bp.route('/reset-session')
def reset_session():
    """Helper route to downgrade current user back to Basic for testing."""
    if g.user:
        from app.db import get_users_db
        from flask import flash, redirect, url_for
        
        db = get_users_db()
        db.execute("UPDATE sessions SET tier='basic', status='PENDING', expiry=NULL WHERE uuid = ?", (g.user['uuid'],))
        db.commit()
        
        flash("Session reset to Free/Basic for testing.", "info")
    
    
    return redirect(url_for('main.index'))

@bp.route('/check-status')
def check_status():
    """Lightweight endpoint for frontend polling."""
    if g.user:
        return {'tier': g.user['tier']}
    return {'tier': 'basic'}
