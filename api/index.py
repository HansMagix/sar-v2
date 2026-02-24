import sys
import os

# Add the project root to Python path so 'app' and 'config' are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import ProductionConfig, DevelopmentConfig

config = ProductionConfig if os.environ.get('VERCEL') else DevelopmentConfig
app = create_app(config)
