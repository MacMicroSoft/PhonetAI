import click
import logging
from flask import Flask, redirect, url_for, request, Blueprint, render_template
from flask.cli import with_appcontext
from flask_admin import Admin, AdminIndexView, expose
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_migrate import Migrate
from flask_restful import Api
from werkzeug.security import check_password_hash

from admin import IntegrationsAdminView, ManagerAdminView, LeadsAdminView, AnalysesAdminView, \
    PhonetAdminView, PhonetLeadsAdminView, AssistantAdminView, PromptsAdmin
from config import Config
from celery_settings import configure_celery, celery
from models import db, User, Integrations, Manager, Leads, Phonet, Analyzes, PhonetLeads, Assistant, Prompts
from api.webhook.router import webhook_route

# Flask redis_config
app = Flask(__name__)

# Use Config class for configuration
app.config.from_object(Config)

# Celery configuration
app.config.update(
    CELERY_BROKER_URL='redis://redis:6379/0',
    CELERY_RESULT_BACKEND='redis://redis:6379/0'
)

# Initialize Flask extensions
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Celery setup

configure_celery(app)

# API and Blueprints
api_bp = Blueprint('api', __name__)
api = Api(api_bp)

app.register_blueprint(webhook_route)


# Admin views
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        return super(MyAdminIndexView, self).index()


admin = Admin(app, name='Admin Panel', template_mode='bootstrap4', index_view=MyAdminIndexView())
admin.add_view(IntegrationsAdminView(Integrations, db.session))
admin.add_view(ManagerAdminView(Manager, db.session))
admin.add_view(LeadsAdminView(Leads, db.session))
admin.add_view(PhonetAdminView(Phonet, db.session))
admin.add_view(AnalysesAdminView(Analyzes, db.session))
admin.add_view(PhonetLeadsAdminView(PhonetLeads, db.session))
admin.add_view(AssistantAdminView(Assistant, db.session))
admin.add_view(PromptsAdmin(Prompts, db.session))


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.index'))
        else:
            return "Invalid credentials", 401

    return render_template('admin/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# CLI command to create superuser
@app.cli.command('createsuperuser')
@click.option('--username', prompt=True, help='The username for the superuser.')
@click.option('--email', prompt=True, help='The email for the superuser.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True,
              help='The password for the superuser.')
@with_appcontext
def create_superuser(username, email, password):
    """Create a superuser"""

    if User.query.filter_by(username=username).first():
        print("User with this username already exists.")
        return

    user = User(username=username, email=email, is_admin=True)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    print(f"Superuser {username} created successfully.")


def create_app():
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Starting Flask app")

    return app


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
