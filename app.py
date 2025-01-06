from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restful import Api

# Ініціалізація бази даних і API
db = SQLAlchemy()
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

from api.webhook.router import hook_bp


def create_app():
    app = Flask(__name__)

    app.config.from_object("config.DevelopmentConfig")

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    app.register_blueprint(api_bp)
    app.register_blueprint(hook_bp, url_prefix='/webhook')

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
