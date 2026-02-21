import sys
import os

# Add the project root to Python path so 'app' and 'config' are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()
