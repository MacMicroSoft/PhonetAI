from sqlalchemy.dialects.postgresql import UUID

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Promt(db.Model):
    __tablename__ = 'Promts'

    id = db.Column(db.Integer, primary_key=True)
    scenario = db.Column(db.String(25), nullable=False)
    roles = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String, nullable=False)
    template = db.Column(db.String, nullable=False)


class Integration(db.Model):
    __tablename__ = 'Integration'

    id = db.Column(db.Integer, primary_key=True)
    subdomain = db.Column(db.String(25), nullable=False)
    link = db.Column(db.String(50), nullable=False)


class Lead(db.Model):
    __tablename__ = 'Leads'

    id = db.Column(db.Integer, primary_key=True)
    main_user_id = db.Column(db.Integer, nullable=False)
    note_type = db.Column(db.Integer, nullable=False)
    uniq = db.Column(db.String(50), nullable=False)  # UUID in string format
    link = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.Integer, default=None, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    integration = db.Column(db.String(10), nullable=False)
    element_id = db.Column(db.Integer, nullable=False)
    timestamp_x = db.Column(db.DateTime, nullable=False)
    account_id = db.Column(db.Integer, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('Manager.id'), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey('Integration.id'), nullable=False)
    created_by = db.Column(db.String(25), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    modified_by = db.Column(db.String(25), nullable=False)
    call_status = db.Column(db.String(5), nullable=True)
    call_result = db.Column(db.String(5), nullable=True)
    path = db.Column(db.String(50), nullable=False)

    # Relationships
    integration_rel = db.relationship('Integration', backref='leads', lazy=True)
    manager_rel = db.relationship('Manager', backref='leads', lazy=True)


class Manager(db.Model):
    __tablename__ = 'Manager'

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(25), nullable=True)
    type = db.Column(db.Integer, nullable=False)

