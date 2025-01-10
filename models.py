import uuid

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, PrimaryKeyConstraint, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from datetime import datetime
from uuid import UUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from typing import Optional, Dict, Any
import json
import re
from urllib.parse import parse_qs, unquote

from flask_sqlalchemy import SQLAlchemy

Base = declarative_base()


# SQLAlchemy моделі

class Integrations(Base):
    __tablename__ = "integrations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    subdomain = Column(String, nullable=False)
    link = Column(String, nullable=False)
    leads = relationship("Leads", back_populates="integration")


class Manager(Base):
    __tablename__ = "manager"
    id = Column(Integer, primary_key=True, autoincrement=True)
    crm_user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    type = Column(Integer, nullable=False)
    leads = relationship("Leads", back_populates="manager")


class Leads(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, nullable=False)
    account_id = Column(Integer, nullable=False)
    element_id = Column(Integer, nullable=False)
    element_type = Column(Integer, nullable=False)
    manager_id = Column(Integer, ForeignKey("manager.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    text_message = Column(Text)
    timestamp_x = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    path = Column(String)
    manager = relationship("Manager", back_populates="leads")
    integration = relationship("Integrations", back_populates="leads")
    phonet_leads = relationship("PhonetLeads", back_populates="lead")


class Phonet(Base):
    __tablename__ = "phonet"
    id = Column(Integer, primary_key=True, autoincrement=True)
    unique_uuid = Column(PGUUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    audio_mp3 = Column(String)
    phone_number = Column(String, nullable=False)
    duration = Column(Integer, nullable=False)
    call_status = Column(Integer, nullable=False)
    call_result = Column(String)
    phonet_leads = relationship("PhonetLeads", back_populates="phonet")


class PhonetLeads(Base):
    __tablename__ = "phonet_leads"
    id = Column(Integer, primary_key=True, autoincrement=True)

    phonet_id = Column(Integer, ForeignKey("phonet.id"), primary_key=True)
    leads_id = Column(Integer, ForeignKey("leads.id"), primary_key=True)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    phonet = relationship("Phonet", back_populates="phonet_leads")
    lead = relationship("Leads", back_populates="phonet_leads")
