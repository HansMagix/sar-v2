import os

# Base directory = project root (where this file lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Detect Vercel serverless environment
IS_VERCEL = os.environ.get('VERCEL', False)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-prod'
    PROGRAMMES_DB = os.path.join(BASE_DIR, 'programmes.db')
    # On Vercel, only /tmp is writable; locally use project root
    USERS_DB = os.path.join('/tmp', 'users.db') if IS_VERCEL else os.path.join(BASE_DIR, 'users.db')
    
    # M-Pesa Configuration
    # Quotes added to fix syntax errors
    MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY') or 'dldlO7MqYDF6IaciHAxRwMLnIavLb8ImFpW8xumtH0SUzhwB'
    MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET') or '2iMHtZ1vPpzDSFeUBe7pe10RLu7L1bwQlKY3tKiJf8my6dWQL19lYLhSvMPTN0yI'
    # Use standard Sandbox Passkey if not provided, or keep user's placeholder if they need to update it
    MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY') or 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919' 
    MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE') or '174379'
    MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL') or 'https://oceanographical-makeda-maximal.ngrok-free.dev/mpesa/callback'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # In production, ensure SECRET_KEY is set in environment
