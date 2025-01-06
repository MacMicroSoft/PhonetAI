from flask import Flask, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_restful import Api

db = SQLAlchemy()
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

from api.webhook.router import hook_bp


def create_app():

    app = Flask(__name__)

    app.config.from_object(f"config.DevelopmentConfig")

    db.init_app(app)

    Migrate(app, db)

    app.register_blueprint(api_bp)
    app.register_blueprint(hook_bp, url_prefix='/webhook')

    return app



def get_elemetns_from_dict():
    pass