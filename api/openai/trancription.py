import os
import logging
from typing import Optional
from functools import wraps

from flask import Response
from openai import OpenAI
from openai.types.beta import thread
from openai import AssistantEventHandler
from dotenv import load_dotenv

from api.openai.decorators import has_permission
from api.openai.placeholders import Thread, Message
from api.webhook.functions.database_orm import save_analyse_data_to_database
from database import SessionLocal
from models import Manager, Assistant, Prompts

load_dotenv()

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])


class AssistanceHandlerOpenAI(AssistantEventHandler):
    def __init__(self, assistant: str, instructions: str, message: str) -> None:
        super().__init__()
        self.__client = client
        self.__assistant_id = assistant or None
        self._instructions = instructions or None
        self._assistant_input = message or None
        self._thread = None

    def create_assistant_thread(self) -> Optional[Thread]:
        logger.info(
            "Creating assistant thread",
            extra={
                "status_code": "100",
                "status_message": "Creating thread",
                "operation_type": "ASSISTANT",
                "service": "FLASK",
            },
        )
        if not self._thread:
            self._thread = self.__client.beta.threads.create()
        return self._thread

    def delete_assistant_thread(self) -> None:
        if self._thread:
            self.__client.beta.threads.delete(thread_id=self._thread.id)
            logger.info(
                "Assistant thread deleted",
                extra={
                    "status_code": "200",
                    "status_message": "Thread deleted",
                    "operation_type": "ASSISTANT",
                    "service": "FLASK",
                },
            )
            self._thread = None

    def create_assistant_message(self) -> Optional[Message]:
        if self._thread:
            logger.info(
                "Creating assistant message",
                extra={
                    "status_code": "100",
                    "status_message": "Creating message",
                    "operation_type": "ASSISTANT",
                    "service": "FLASK",
                },
            )
            message = self.__client.beta.threads.messages.create(
                thread_id=self._thread.id,
                role="user",
                content=self._assistant_input,
            )
            return message
        else:
            logger.error(
                "Thread not created before message",
                extra={
                    "status_code": "400",
                    "status_message": "Thread missing",
                    "operation_type": "ASSISTANT",
                    "service": "FLASK",
                },
            )
            raise ValueError("Thread is not created yet.")

    def create_assistant_run(self) -> Optional[object]:
        if not self._thread:
            self.create_assistant_thread()

        logger.info(
            "Running assistant",
            extra={
                "status_code": "100",
                "status_message": "Assistant run started",
                "operation_type": "ASSISTANT",
                "service": "FLASK",
            },
        )

        with self.__client.beta.threads.runs.stream(
            thread_id=self._thread.id,
            assistant_id=self.__assistant_id,
            instructions=self._instructions,
            model="gpt-4o-mini",
        ) as stream:
            stream.until_done()
            return stream


def get_first_active_assistant():
    with SessionLocal() as db:
        result = (
            db.query(Assistant.assistant_id, Assistant.message_prompt)
            .filter(Assistant.is_active == True)
            .first()
        )
        if result:
            logger.info(
                "Active assistant found",
                extra={
                    "status_code": "200",
                    "status_message": "Assistant loaded",
                    "operation_type": "ASSISTANT",
                    "service": "FLASK",
                },
            )
            return {"assistant_id": result[0], "message_promt": result[1]}

        logger.warning(
            "No active assistant found",
            extra={
                "status_code": "400",
                "status_message": "No assistant found",
                "operation_type": "ASSISTANT",
                "service": "FLASK",
            },
        )
        return None


def transcriptions(audio_file_mp3_path: str):
    try:
        logger.info(
            "Starting transcription",
            extra={
                "status_code": "100",
                "status_message": "Transcription started",
                "operation_type": "TRANSCRIPTION",
                "service": "FLASK",
            },
        )
        with open(audio_file_mp3_path, "rb") as audio_file_mp3:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_mp3,
            )
            if transcription:
                logger.info(
                    "Transcription completed",
                    extra={
                        "status_code": "200",
                        "status_message": "Transcribed",
                        "operation_type": "TRANSCRIPTION",
                        "service": "FLASK",
                    },
                )
                return transcription.text
    except FileNotFoundError as f:
        logger.error(
            f"Transcription failed: file not found - {f}",
            exc_info=True,
            extra={
                "status_code": "400",
                "status_message": "File not found",
                "operation_type": "TRANSCRIPTION",
                "service": "FLASK",
            },
        )
    except IOError as o:
        logger.error(
            f"Transcription failed: IO error - {o}",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "IO error",
                "operation_type": "TRANSCRIPTION",
                "service": "FLASK",
            },
        )
    except Exception as e:
        logger.error(
            f"Unexpected transcription error: {type(e).__name__} - {e}",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "Unknown transcription error",
                "operation_type": "TRANSCRIPTION",
                "service": "FLASK",
            },
        )
        raise e


def assistant_start(transcrip_text: str, crm_data_json: dict, crm_manager):
    logger.info(
        "Assistant start initiated",
        extra={
            "status_code": "100",
            "status_message": "Assistant starting",
            "operation_type": "ASSISTANT",
            "service": "FLASK",
        },
    )

    assistant_check = get_first_active_assistant()

    if not assistant_check:
        logger.warning(
            "Assistant not found",
            extra={
                "status_code": "400",
                "status_message": "No assistant available",
                "operation_type": "ASSISTANT",
                "service": "FLASK",
            },
        )
        return "Not found assistant."

    handler = AssistanceHandlerOpenAI(
        assistant=assistant_check["assistant_id"],
        instructions=assistant_check["message_promt"],
        message=str(transcrip_text),
    )

    handler.create_assistant_thread()
    handler.create_assistant_message()
    response = handler.create_assistant_run()

    if response:
        response_message = response.get_final_messages()[0]
        gpt_answer = response_message.content[0].text.value

        logger.info(
            "Assistant completed successfully",
            extra={
                "status_code": "200",
                "status_message": "Assistant success",
                "operation_type": "ASSISTANT",
                "service": "FLASK",
            },
        )

        analysed_json = {
            "lead_id": crm_data_json["lead_id"],
            "audio_text": transcrip_text,
            "analysed_text": gpt_answer,
            "is_analysed": True,
        }

        save_analyse_data_to_database(analysed_json)
        crm_manager.post_send_data_to_crm(
            lead_id=crm_data_json["lead_element_id"],
            content=str(gpt_answer),
        )
    else:
        logger.error(
            "Assistant response is empty",
            extra={
                "status_code": "500",
                "status_message": "No response",
                "operation_type": "ASSISTANT",
                "service": "FLASK",
            },
        )

    handler.delete_assistant_thread()
