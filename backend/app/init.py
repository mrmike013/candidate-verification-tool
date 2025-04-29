from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from ..config import Config

# Global singleton db so models can import it

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensions
    db.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    # Blueprints / routes
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    # CLI seed command (optional)
    from .seed import seed_cmd
    app.cli.add_command(seed_cmd)

    with app.app_context():
        db.create_all()

    return app
