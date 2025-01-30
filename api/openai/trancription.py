import os
import time
import logging
from flask import Response, abort
from openai import OpenAI
from typing import Optional
from functools import wraps

from dotenv import load_dotenv
from openai.types.beta import thread

from typing_extensions import override
from openai import AssistantEventHandler

from api.openai.decorators import has_permission
from api.openai.placeholders import Thread, Message
from api.webhook.functions.database_orm import save_analyse_data_to_database
from database import SessionLocal
from models import Manager, Assistant, Prompts

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])


class AssistanceHandlerOpenAI(AssistantEventHandler):
    def __init__(self, assistant: str, instructions: str, message: str, system_content: str, promt_type: str) -> None:
        super().__init__()
        self.__client = client
        self.__assistant_id = assistant or None
        self._instructions = instructions or None
        self._assistant_input = message or None
        self.promt_type = promt_type
        self._system_content = system_content or None
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

    def create_assistant(self, name, desc, model):
        """ Create assistant (DON'T USE NOW, Mby in future)"""
        assistant = self.__client.beta.assistants.create(
            name=name,
            description=desc,
            model=model,
        )
        return assistant

    def update_assistant(self):
        my_updated_assistant = client.beta.assistants.update(
            assistant_id=self.__assistant_id,
            instructions=self._system_content,
        )

    def change_assistant_system_promts(self, assistant_id):
        assistant = self.__client.beta.assistants.update(
            assistant_id=assistant_id,
            instructions=self._instructions,
        )

    def create_assistant_thread(self) -> Optional[Thread]:
        """Create new thread."""

        if not self._thread:
            self._thread = self.__client.beta.threads.create(
            )

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


@staticmethod
def transcriptions(audio_file_mp3_path: str):
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


def get_first_active_assistant():
    with SessionLocal() as db:
        # Query the Assistant table and also include prompt_type and content from the Prompts table
        result = db.query(Assistant, Prompts.prompt_type, Prompts.content) \
            .join(Prompts, Prompts.assistant_id == Assistant.id) \
            .filter(Assistant.is_active == True, Prompts.is_active == True) \
            .first()

        if result:
            # Extract the assistant instance, prompt_type, and content
            assistant = result[0]  # Assistant instance
            prompt_type = result[1]  # Prompt type from Prompts
            content = result[2]  # Content from Prompts
            return {
                "assistant_id": assistant.assistant_id,
                "message_promt": assistant.message_promt,
                "prompt_type": prompt_type,
                "content": content
            }
        return None


def assistant_start(transcrip_text: str, crm_data_json: dict, crm_manager):
    """Start the assistant process with an audio file."""
    assistant_check = get_first_active_assistant()
    assistant_id = assistant_check.get('assistant_id')
    message_promt = assistant_check.get('message_promt')
    content = assistant_check.get('content')
    prompt_type = assistant_check.get('prompt_type')

    if assistant_check is not None:
        handler = AssistanceHandlerOpenAI(
            assistant=assistant_id,
            instructions=message_promt,
            message=str(transcrip_text),
            system_content=content,
            promt_type=prompt_type
        )
        # handler.update_assistant()
        handler.create_assistant_thread()
        handler.create_assistant_message()

        response = handler.create_assistant_run()

        if response:
            response_message = response.get_final_messages()[0]
            gpt_answer = response_message.content[0].text.value
            logger.info("Assistant run completed successfully.")

            analysed_json = {"lead_id": crm_data_json["lead_id"],
                             "audio_text": transcrip_text,
                             "analysed_text": gpt_answer,
                             "is_analysed": True
                             }

            save_analyse_data_to_database(analysed_json)
            crm_manager.post_send_data_to_crm(lead_id=crm_data_json["lead_element_id"], content=str(gpt_answer))
        else:
            logger.error("Assistant run failed.")

        handler.delete_assistant_thread()
    else:
        return "Not found assistant."
