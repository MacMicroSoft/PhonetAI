from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class Integrations:
    subdomain: Optional[str] = None
    link: Optional[str] = None

@dataclass
class Manager:
    crm_user_id: Optional[int] = None
    username: Optional[str] = None
    type: Optional[str] = None

@dataclass
class Leads:
    owner_id: Optional[int] = None
    account_id: Optional[int] = None
    element_id: Optional[int] = None
    element_type: Optional[int] = None
    text_message: Optional[str] = None
    timestamp_x: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    lead_status: Optional[str] = None

@dataclass
class PhonetLeads:
    last_update: Optional[datetime] = None

@dataclass
class Phonet:
    unique_uuid: Optional[UUID] = None
    audio_mp3: Optional[str] = None
    phone_number: Optional[str] = None
    duration: Optional[int] = None
    call_status: Optional[int] = None
    call_result: Optional[int] = None
