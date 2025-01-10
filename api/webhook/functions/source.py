from urllib.parse import parse_qs, unquote
import json
import re
from sqlalchemy.orm import relationship, Session
from pprint import pprint
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

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
    path: Optional[str] = None


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


class HookDecoder:
    def __init__(self) -> None:
        self.__clear_data: dict = {}

    def webhook_decoder(self, raw_data: str, return_data: bool = False) -> None | Dict[str, Any]:
        logger.info(
            "Start decoding data",
            extra={
                "status_code": "100",
                "status_message": "DATA",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

        decoded_data: str = unquote(raw_data)
        parsed_data: dict = parse_qs(decoded_data)

        for key in parsed_data:
            if isinstance(parsed_data[key], list) and len(parsed_data[key]) == 1:
                try:
                    short_key: str = re.findall(r"\[(.*?)\]", key)[-1]
                    self.__clear_data[short_key] = json.loads(parsed_data[key][0])
                except json.JSONDecodeError:
                    cleaned_value: str | int = re.sub(r'\\n"|\\', '', parsed_data[key][0])

                    if cleaned_value.isdigit():
                        cleaned_value = int(cleaned_value)

                    self.__clear_data[short_key] = cleaned_value

        if return_data:
            logger.info(
                "Successful decode data",
                extra={
                    "status_code": "100",
                    "status_message": "DATA",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )

            return self.__clear_data

    def table_map(self) -> Dict[str, Dict[str, Any]]:
        logger.info(
            "Start parse data",
            extra={
                "status_code": "100",
                "status_message": "DATA",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

        if not isinstance(self.__clear_data, dict):
            logger.info(
                "Wrong dict type",
                extra={
                    "status_code": "422",
                    "status_message": "Unprocessable Entity",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                    "extra": {type(self.__clear_data)},
                },
            )

        logger.info(
            "Successful parse data",
            extra={
                "status_code": "100",
                "status_message": "DATA",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

        return {
            "Integrations": asdict(Integrations(
                subdomain=self.__clear_data.get("subdomain"),
                link=self.__clear_data.get("self"),
            )),
            "Manager": asdict(Manager(
                crm_user_id=self.__clear_data.get("metadata", {}).get("event_source", {}).get("id"),
                username=self.__clear_data.get("metadata", {}).get("event_source", {}).get("author_name"),
                type=self.__clear_data.get("metadata", {}).get("event_source", {}).get("type"),
            )),
            "Leads": asdict(Leads(
                owner_id=self.__clear_data.get("main_user_id"),
                account_id=self.__clear_data.get("main_user_id"),
                element_id=self.__clear_data.get("element_id"),
                element_type=self.__clear_data.get("element_type"),
                text_message=self.__clear_data.get("text") if isinstance(self.__clear_data.get("text"), str) else None,
                timestamp_x=self.__clear_data.get("timestamp_x"),
                created_at=datetime.utcfromtimestamp(self.__clear_data.get("created_at")).strftime('%Y-%m-%d %H:%M:%S'),
                updated_at=datetime.utcfromtimestamp(self.__clear_data.get("updated_at")).strftime('%Y-%m-%d %H:%M:%S'),
                path=self.__clear_data.get("unknows"),
            )),
            "PhonetLeads": asdict(PhonetLeads(
                last_update=None,
            )),
            "Phonet": {} if isinstance(self.__clear_data.get("text"), str) else asdict(Phonet(
                unique_uuid=self.__clear_data.get("text", {}).get("UNIQ"),
                audio_mp3=self.__clear_data.get("unknows"),
                phone_number=self.__clear_data.get("text", {}).get("PHONE").lstrip(),
                duration=self.__clear_data.get("text", {}).get("DURATION"),
                call_status=self.__clear_data.get("text", {}).get("call_status"),
                call_result=self.__clear_data.get("unknows"),
            )),
        }
