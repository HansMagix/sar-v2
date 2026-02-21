from app.db import get_users_db
import datetime

def get_session(uuid):
    db = get_users_db()
    return db.execute("SELECT * FROM sessions WHERE uuid = ?", (uuid,)).fetchone()

def create_session(uuid, phone="Unknown"):
    db = get_users_db()
    # Default expiry one year from now just for data cleanliness, though free tier doesn't expire really
    expiry = datetime.datetime.now() + datetime.timedelta(days=365)
    
    db.execute('''
        INSERT OR IGNORE INTO sessions (uuid, phone, tier, status, expiry)
        VALUES (?, ?, 'free', 'active', ?)
    ''', (uuid, phone, expiry))
    db.commit()
    
    return get_session(uuid)

def update_tier(uuid, tier, mpesa_ref=None):
    db = get_users_db()
    # Set expiry to 24 hours from now for 24h pass
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
    
    db.execute('''
        UPDATE sessions 
        SET tier = ?, status = 'active', expiry = ?, mpesa_ref = ?
        WHERE uuid = ?
    ''', (tier, expiry, mpesa_ref, uuid))
    db.commit()
