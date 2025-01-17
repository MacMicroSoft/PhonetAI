import sys
import redis
from flask import Flask, Blueprint
from flask_migrate import Migrate
from flask_restful import Api
from models import *  # Assuming models are defined in another file
import os
import logging

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

from api.webhook.router import hook_bp


def create_app():
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Info log information")

    app.config.from_object("config.ProdConfig")
    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(api_bp)
    app.register_blueprint(hook_bp, url_prefix='/webhook')

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(host="0.0.0.0", port=8000)
