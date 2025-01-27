import os
import time
import logging
from flask import Response, abort
from openai import OpenAI
from typing import Optional
from functools import wraps

from dotenv import load_dotenv
from openai.types.beta import thread, Assistant
from typing_extensions import override
from openai import AssistantEventHandler

from api.openai.decorators import has_permission
from api.openai.placeholders import Thread, Message
from api.webhook.functions.database_orm import save_analyse_data_to_database
from models import Manager

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AssistanceHandlerOpenAI(AssistantEventHandler):
    def __init__(self, client: OpenAI, assistant: str, instructions: str, message: str):
        super().__init__()
        self.__client = client
        self.__assistant_id = assistant
        self._instructions = instructions
        self._assistant_input = message
        self._thread = None

    @staticmethod
    def transcriptions(client: OpenAI, audio_file_mp3_path: str) -> str:
        """
        Use transcription to get text from mp3 for analyse in assistant.
        return transcription text
        """
        try:
            with open(audio_file_mp3_path, "rb") as audio_file_mp3:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file_mp3
                )
                if transcription:
                    return transcription.text

        except FileNotFoundError as f:
            logger.error(f"Error: File not found. Details: {f}")
        except IOError as o:
            logger.error(f"Error: I/O error occurred. Details: {o}")
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__} - {e}")
            raise e

    def create_assistant(self) -> Optional[Assistant]:
        """ Create assistant (DON'T USE NOW, Mby in future)"""
        assistant = self.__client.beta.assistants.create(
            name="Assistant_Name",
            description="desc",  # Here should be promt mby
            model="gpt-4o",
        )
        return assistant

    def create_assistant_thread(self) -> Optional[Thread]:
        """Create new thread."""
        if not self._thread:
            self._thread = self.__client.beta.threads.create()
        return self._thread

    def delete_assistant_thread(self) -> None:
        if self._thread:
            self.__client.beta.threads.delete(thread_id=self._thread.id)
            self._thread = None

    def create_assistant_message(self) -> Optional[Message]:
        """Add a user message to the assistant thread."""
        if self._thread:
            message = self.__client.beta.threads.messages.create(
                thread_id=self._thread.id,
                role="user",
                content=self._assistant_input,
            )
            return message
        else:
            raise ValueError("Thread is not created yet.")

    def create_assistant_run(self) -> Optional[object]:
        """Run assistant with instructions and stream response."""
        if not self._thread:
            self.create_assistant_thread()

        with self.__client.beta.threads.runs.stream(
                thread_id=self._thread.id,
                assistant_id=self.__assistant_id,
                instructions=self._instructions,
                model="gpt-3.5-turbo",
        ) as stream:
            stream.until_done()
            return stream


client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

@staticmethod
def transcriptions(audio_file_mp3_path) -> str:
    """
    Use transcription to get text from mp3 for analyse in assistant.
    return transcription text
    """
    try:
        with open(audio_file_mp3_path, "rb") as audio_file_mp3:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_mp3
            )
            if transcription:
                return transcription.text

    except FileNotFoundError as f:
        logger.error(f"Error: File not found. Details: {f}")
    except IOError as o:
        logger.error(f"Error: I/O error occurred. Details: {o}")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__} - {e}")
        raise e


@has_permission
def assistant_start(transcrip_text: str, crm_data_json: dict, crm_manager):
    """Start the assistant process with an audio file."""
    print("START SENDINGGG")
    handler = AssistanceHandlerOpenAI(
        client=client,
        assistant=os.getenv('OPENAI_ASSISTANT_NAME'),
        instructions=os.getenv('OPENAI_ASSISTANT_INSTRUCTIONS'),
        message=str(transcrip_text)
    )

    handler.create_assistant_thread()
    handler.create_assistant_message()

    response = handler.create_assistant_run()

    if response:
        response_message = response.get_final_messages()[0]
        gpt_answer = response_message.content[0].text.value
        logger.info("Assistant run completed successfully.")
        print(gpt_answer)

        analysed_json = {"lead_id": crm_data_json["lead_id"],
                         "audio_text": transcrip_text,
                         "analysed_text": gpt_answer,
                         "is_analysed": True
                         }

        save_analyse_data_to_database(analysed_json)
        crm_manager.post_send_data_to_crm(lead_id=crm_data_json["lead_element_id"], content=str(gpt_answer))
    else:
        logger.error("Assistant run failed.")

    # handler.delete_assistant_thread()