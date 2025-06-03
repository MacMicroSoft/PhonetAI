import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from urllib.parse import parse_qs, unquote

import requests

from dataclasses import Integrations, Manager, Leads, Phonet, PhonetLeads, asdict
from api.openai.decorators import has_permission

logger = logging.getLogger(__name__)


class AudioManager:
    def __init__(self) -> None:
        self.__audio_path = Path("./static/audio")
        self.__audio_path.mkdir(parents=True, exist_ok=True)

    @has_permission
    def download(self, url: str, uniq_uuid: str, manager_id: int) -> Path:
        try:
            logger.info(
                "Downloading audio",
                extra={
                    "status_code": "100",
                    "status_message": "Downloading audio file",
                    "operation_type": "AUDIO",
                    "service": "FLASK",
                },
            )
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.RequestException:
            logger.error(
                "Audio download failed",
                exc_info=True,
                extra={
                    "status_code": "500",
                    "status_message": "Audio download error",
                    "operation_type": "AUDIO",
                    "service": "FLASK",
                },
            )
            raise

        path = self.__audio_path / f"{uniq_uuid}.mp3"
        try:
            with open(path, "wb") as f:
                f.write(response.content)
            logger.info(
                "Audio saved",
                extra={
                    "status_code": "200",
                    "status_message": "Audio file saved",
                    "operation_type": "AUDIO",
                    "service": "FLASK",
                },
            )
            return path
        except Exception:
            logger.error(
                "Audio save failed",
                exc_info=True,
                extra={
                    "status_code": "500",
                    "status_message": "Audio save error",
                    "operation_type": "AUDIO",
                    "service": "FLASK",
                },
            )
            raise

    def delete(self, audio_path: Path) -> None:
        try:
            audio_path.unlink()
            logger.info(
                "Audio deleted",
                extra={
                    "status_code": "200",
                    "status_message": "Audio file deleted",
                    "operation_type": "AUDIO",
                    "service": "FLASK",
                },
            )
        except Exception:
            logger.warning(
                "Audio delete failed",
                exc_info=True,
                extra={
                    "status_code": "400",
                    "status_message": "Audio delete error",
                    "operation_type": "AUDIO",
                    "service": "FLASK",
                },
            )

    @property
    def get_audio_folder(self) -> Path:
        return self.__audio_path


class HookDecoder:
    def __init__(self) -> None:
        self.__clear_data: dict = {}
        self.__is_phonet: bool = False

    @property
    def is_phonet(self) -> bool:
        return self.__is_phonet

    def webhook_decoder(self, raw_data: str, return_data: bool = False) -> Optional[Dict[str, Any]]:
        logger.info(
            "Decoding webhook data",
            extra={
                "status_code": "100",
                "status_message": "Start decoding",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

        decoded_data = unquote(raw_data)
        parsed_data = parse_qs(decoded_data)

        for key, value in parsed_data.items():
            if isinstance(value, list) and len(value) == 1:
                try:
                    short_key = re.findall(r"\[(.*?)\]", key)[-1]
                    self.__clear_data[short_key] = json.loads(value[0])
                except json.JSONDecodeError:
                    cleaned = re.sub(r'\\n"|\\', '', value[0])
                    self.__clear_data[short_key] = int(cleaned) if cleaned.isdigit() else cleaned

        self.__is_phonet = not isinstance(self.__clear_data.get("text"), str)

        if return_data:
            logger.info(
                "Webhook data decoded",
                extra={
                    "status_code": "200",
                    "status_message": "Decoded successfully",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )
            return self.__clear_data

    def integration_data(self) -> Optional[tuple[str, str, int, str]]:
        if self.__is_phonet:
            return (
                self.__clear_data.get("text", {}).get("UNIQ"),
                self.__clear_data.get("text", {}).get("LINK"),
                self.__clear_data.get("element_id"),
                self.__clear_data.get("self"),
            )
        return None

    def table_map(self, lead_status: str) -> Dict[str, Dict[str, Any]]:
        logger.info(
            "Mapping data to model",
            extra={
                "status_code": "100",
                "status_message": "Mapping started",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

        created_at = self.__clear_data.get("created_at")
        updated_at = self.__clear_data.get("updated_at")

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
                created_at=datetime.utcfromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S') if created_at else None,
                updated_at=datetime.utcfromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S') if updated_at else None,
                lead_status=lead_status if self.__is_phonet else "",
            )),
            "PhonetLeads": asdict(PhonetLeads()),
            "Phonet": {} if not self.__is_phonet else asdict(Phonet(
                unique_uuid=self.__clear_data.get("text", {}).get("UNIQ"),
                audio_mp3=self.__clear_data.get("text", {}).get("LINK"),
                phone_number=self.__clear_data.get("text", {}).get("PHONE").lstrip(),
                duration=self.__clear_data.get("text", {}).get("DURATION"),
                call_status=self.__clear_data.get("text", {}).get("call_status"),
                call_result=self.__clear_data.get("text", {}).get("call_result"),
            )),
        }
