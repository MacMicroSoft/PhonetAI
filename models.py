import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)


class Integrations(db.Model):
    __tablename__ = "integrations"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subdomain = db.Column(db.String, nullable=False)
    link = db.Column(db.String, nullable=False)
    leads = db.relationship("Leads", back_populates="integration")


class Manager(db.Model):
    __tablename__ = "manager"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crm_user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String, nullable=False)
    type = db.Column(db.Integer, nullable=False)
    leads = db.relationship("Leads", back_populates="manager")
    is_permissions = db.Column(db.Boolean, nullable=True, default=False)


class Leads(db.Model):
    __tablename__ = "leads"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, nullable=False)
    account_id = db.Column(db.Integer, nullable=False)
    element_id = db.Column(db.Integer, nullable=False)
    element_type = db.Column(db.Integer, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey("manager.id"), nullable=False)
    integration_id = db.Column(db.Integer, db.ForeignKey("integrations.id"), nullable=False)
    text_message = db.Column(db.Text)
    timestamp_x = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lead_status = db.Column(db.String, nullable=True)
    manager = db.relationship("Manager", back_populates="leads")
    integration = db.relationship("Integrations", back_populates="leads")
    phonet_leads = db.relationship("PhonetLeads", back_populates="lead")


class Phonet(db.Model):
    __tablename__ = "phonet"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    unique_uuid = db.Column(PGUUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    audio_mp3 = db.Column(db.String)
    phone_number = db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    call_status = db.Column(db.Integer, nullable=False)
    call_result = db.Column(db.String)
    phonet_leads = db.relationship("PhonetLeads", back_populates="phonet")


class Analyzes(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=False)
    audio_text = db.Column(db.String)
    analysed_text = db.Column(db.String, default=None)
    is_analysed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class PhonetLeads(db.Model):
    __tablename__ = "phonet_leads"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phonet_id = db.Column(db.Integer, db.ForeignKey("phonet.id"))
    leads_id = db.Column(db.Integer, db.ForeignKey("leads.id"))
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    phonet = db.relationship("Phonet", back_populates="phonet_leads")
    lead = db.relationship("Leads", back_populates="phonet_leads")


class Assistant(db.Model):
    __tablename__ = "assistant"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assistant_name = db.Column(db.String, nullable=False)
    assistant_id = db.Column(db.String, nullable=True, unique=True, default=None)
    model = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    message_promt = db.Column(db.String, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=False)


class Prompts(db.Model):
    __tablename__ = "prompts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    assistant_id = db.Column(db.Integer, db.ForeignKey("assistant.id"), nullable=False)

    prompt_type = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)

    assistant = db.relationship("Assistant", backref="prompts")


class ActivePrompts(db.Model):
    __tablename__ = "active_prompts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    assistant_id = db.Column(db.String, db.ForeignKey("assistant.assistant_id"), nullable=False, unique=True)
    active_system_prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=False)
    active_message_prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=False)