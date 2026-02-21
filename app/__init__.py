from flask import Flask
from config import DevelopmentConfig

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from . import db
    db.init_app(app)

    # Initialize users db on app start for simplicity in this scaffold
    # In production, this might be a separate migration command
    with app.app_context():
        db.init_users_db()

    # Import and register blueprints
    # Import and register blueprints
    from app.routes import main, auth, payments, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(payments.bp)
    app.register_blueprint(admin.bp)
    
    @app.route('/health')
    def health():
        return {'status': 'ok'}

    return app
