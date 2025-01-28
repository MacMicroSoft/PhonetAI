from urllib.parse import parse_qs, unquote
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
import logging
import requests

from api.openai.decorators import has_permission

logger = logging.getLogger(__name__)


class AudioManager:
    def __init__(self) -> None:
        self.__audio_path: Path = Path("./static/audio")
        self.__audio_path.mkdir(parents=True, exist_ok=True)

    @has_permission
    def download(self, url: str, uniq_uuid: str, manager_id: int) -> Path:
        """
        Завантажує аудіофайл за URL і зберігає його локально.
        """
        try:
            logger.info(f"Downloading audio file from URL: {url}")
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download audio file: {e}")
            raise

        downloaded_path: Path = self.__audio_path / f"{uniq_uuid}.mp3"
        try:
            with open(downloaded_path, "wb") as file:
                file.write(response.content)
            logger.info(f"File successfully downloaded to: {downloaded_path}")
            return downloaded_path
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            raise


    def delete(self, audio_path: Path) -> None:
        """Видаляє аудіо за його адресою розташування"""
        # try:
        print(audio_path, "PATH")
        audio_path.unlink()
        print("Audio видалене успішно")
        # except:
        #     print("Audio видалене або не було заввнтажене")

    @property
    def get_audio_folder(self) -> Path:
        return self.__audio_path


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


class HookDecoder:
    def __init__(self) -> None:
        self.__clear_data: dict = {}
        self.__is_phonet: bool = False

    @property
    def is_phonet(self) -> bool:
        return self.__is_phonet

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

        self.__is_phonet: bool = False if isinstance(self.__clear_data.get("text"), str) else True

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

    def integration_data(self) -> tuple[Literal["unique_uuid", "audio_mp3", "element_id", "domain"]] | None:
        """Якщо Phonet Повертає дані:\nunique_uuid -> Імя файлу.mp3\naudio_mp3 -> путь для завантаження файлу\nelement_id -> ID ліда"""
        if self.__is_phonet:
            return (
                self.__clear_data.get("text", {}).get("UNIQ"),
                self.__clear_data.get("text", {}).get("LINK"),
                self.__clear_data.get("element_id"),
                self.__clear_data.get("self"),
            )
        return

    def table_map(self, lead_status: str) -> Dict[str, Dict[str, Any]]:
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
                lead_status=lead_status if self.__is_phonet else "",
            )),
            "PhonetLeads": asdict(PhonetLeads(
                last_update=None,
            )),
            "Phonet": {} if not self.__is_phonet else asdict(Phonet(
                unique_uuid=self.__clear_data.get("text", {}).get("UNIQ"),
                audio_mp3=self.__clear_data.get("text", {}).get("LINK"),
                phone_number=self.__clear_data.get("text", {}).get("PHONE").lstrip(),
                duration=self.__clear_data.get("text", {}).get("DURATION"),
                call_status=self.__clear_data.get("text", {}).get("call_status"),
                call_result=self.__clear_data.get("text", {}).get("call_result"),
            )),
        }


class ApiCRMManager:
    def __init__(self, base_url: str, access_token: str) -> None:
        self.__base_url: str = base_url + "/api/v4/"
        self.__access_token: str = access_token
        self.__headers = {
            "Authorization": f"Bearer {self.__access_token}"
        }

    def refresh_token(self, new_token: str) -> None:
        """Update access token"""
        self.__access_token = new_token
        self.__headers["Authorization"] = f"Bearer {self.__access_token}"

    def __request_pack(self, url: str) -> dict:
        """DRY Method"""
        try:
            response = requests.get(url, headers=self.__headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return {}

    @property
    def lead_info(self):
        """Get info about Lead"""

        def getter(lead_id: int) -> dict:
            url = f"{self.__base_url}leads/{lead_id}"
            return self.__request_pack(url)

        return getter

    @property
    def pipeline_info(self):
        """Get info about Pipeline"""

        def getter(pipeline_id: int) -> dict:
            url = f"{self.__base_url}leads/pipelines/{pipeline_id}"
            return self.__request_pack(url)

        return getter

    @property
    def status_info_args(self):
        """Get statuse info from Pipeline"""

        def getter(pipeline_id: int, status_id: int) -> dict:
            url = f"{self.__base_url}leads/pipelines/{pipeline_id}/statuses/{status_id}"
            return self.__request_pack(url)

        return getter

    @property
    def status_info(self):
        """Get statuse info"""

        def getter(lead_id: int) -> dict:
            lead_info: dict = self.lead_info(lead_id)
            url = f"{self.__base_url}leads/pipelines/{lead_info.get('pipeline_id')}/statuses/{lead_info.get('status_id')}"
            return self.__request_pack(url)

        return getter

    def post_send_data_to_crm(self, lead_id: int, content: str) -> None:
        if not self.__access_token:
            return

        url = f"{self.__base_url}leads/{lead_id}/notes"
        headers = {
            "Authorization": f"Bearer {self.__access_token}",
            "Content-Type": "application/json"
        }
        payload = [
            {"note_type": "common", "params": {"text": content}}
        ]
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
        except requests.RequestException as error:
            return
