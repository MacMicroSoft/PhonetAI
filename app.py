import os
import logging
import sys
import redis
from flask import Flask, Blueprint
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask import Flask, render_template
from flask_basicauth import BasicAuth
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_restful import Api
from api.admin import *
from models import *

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

from api.webhook.router import hook_bp
from api.auth.auth import auth

def create_app():
    app = Flask(__name__)

    admin = Admin(app, name='microblog', template_mode='bootstrap4')
    admin.add_view(UserAdminView(User, db.session))
    admin.add_view(IntegrationsAdminView(Integrations, db.session))
    admin.add_view(ManagerAdminView(Manager, db.session))
    admin.add_view(LeadsAdminView(Leads, db.session))
    admin.add_view(PhonetAdminView(Phonet, db.session))
    admin.add_view(AnalysesAdminView(Analyses, db.session))
    admin.add_view(PhonetLeadsAdminView(PhonetLeads, db.session))

    logging.basicConfig(level=logging.INFO)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Info log information")

    app.config.from_object("config.ProdConfig")
    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(api_bp)
    app.register_blueprint(hook_bp, url_prefix='/webhook')
    app.register_blueprint(auth, url_prefix='/auth')

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(host="0.0.0.0", port=8000)
