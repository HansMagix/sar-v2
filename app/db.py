import sqlite3
import datetime
from flask import g, current_app

def get_programmes_db():
    if 'programmes_db' not in g:
        g.programmes_db = sqlite3.connect(
            current_app.config['PROGRAMMES_DB'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.programmes_db.row_factory = sqlite3.Row
    return g.programmes_db

def get_users_db():
    if 'users_db' not in g:
        g.users_db = sqlite3.connect(
            current_app.config['USERS_DB'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.users_db.row_factory = sqlite3.Row
    return g.users_db

def close_db(e=None):
    programmes_db = g.pop('programmes_db', None)
    if programmes_db is not None:
        programmes_db.close()

    users_db = g.pop('users_db', None)
    if users_db is not None:
        users_db.close()

def init_users_db():
    db = get_users_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            uuid TEXT PRIMARY KEY,
            phone TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'free',
            status TEXT NOT NULL DEFAULT 'active',
            expiry TIMESTAMP,
            mpesa_ref TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_uuid TEXT NOT NULL,
            mpesa_code TEXT UNIQUE NOT NULL,
            amount INTEGER DEFAULT 50,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_uuid) REFERENCES sessions(uuid)
        )
    ''')
    db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
