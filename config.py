import os

# Base directory = project root (where this file lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Detect Vercel serverless environment
IS_VERCEL = os.environ.get('VERCEL', False)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
    PROGRAMMES_DB = os.path.join(BASE_DIR, 'programmes.db')
    # On Vercel, only /tmp is writable; locally use project root
    USERS_DB = os.path.join('/tmp', 'users.db') if IS_VERCEL else os.path.join(BASE_DIR, 'users.db')
    
    # Admin dashboard access key
    ADMIN_KEY = os.environ.get('ADMIN_KEY', 'admin123')
    
    # M-Pesa Configuration (set via environment variables only)
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '')
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL', '')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # In production, ensure SECRET_KEY is set in environment
