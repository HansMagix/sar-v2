from app import create_app
from app.db import get_users_db
import sqlite3

app = create_app()
with app.app_context():
    db = get_users_db()
    try:
        db.execute("ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT 'PENDING'")
        print("Added status column.")
    except sqlite3.OperationalError:
        print("status column likely exists.")
        
    try:
        db.execute("ALTER TABLE transactions ADD COLUMN amount INTEGER DEFAULT 50")
        print("Added amount column.")
    except sqlite3.OperationalError:
        print("amount column likely exists.")
    
    db.commit()
    print("Migration complete.")
