import hashlib
import os
import redis
import logging
from dotenv import load_dotenv
from flask import Blueprint, request, Response

from api.openai.trancription import assistant_start, transcriptions
from api.webhook.functions.database_orm import save_to_database
from api.webhook.functions.source import AudioManager, ApiCRMManager, HookDecoder
from celery_settings import celery

logger = logging.getLogger(__name__)
load_dotenv()
webhook_route = Blueprint('webhook', __name__)

redis_client = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))


def get_app():
    from app import app
    return app


@webhook_route.route('/como/crm/', methods=['POST'])
def webhook_from_CRM():
    try:
        if request.method != 'POST':
            logger.warning("Only POST method is allowed")
            return Response("Only POST method is allowed.", status=405)

        data = request.get_data()
        hash_data = hashlib.sha256(data).hexdigest()

        REDIS_EXPIRE_TIME = 180
        if redis_client.exists(hash_data):
            logger.info("Duplicate data received, ignoring")
            return Response("Duplicate data received, ignoring.", status=200)
        redis_client.set(hash_data, 1, ex=REDIS_EXPIRE_TIME)

        process_webhook_data.delay(data)

        logger.info("Webhook received and processing started")
        return Response("Webhook received and processing started", status=200)

    except Exception as e:
        logger.error("Error processing request: %s", e)
        return Response(f"Error processing request: {e}", status=500)


@celery.task
def process_webhook_data(data):
    try:
        app = get_app()
        with app.app_context():
            hook_decod = HookDecoder()
            hook_decod.webhook_decoder(raw_data=data)

            audio_filename, audio_url, lead_id, url_domain = hook_decod.integration_data()
            logger.info("Отримано дані: %s, %s, %s, %s", audio_filename, audio_url, lead_id, url_domain)

            try:
                crm_manager = ApiCRMManager(url_domain, access_token=os.getenv('ACCESS_TOKEN'))
                lead_status_str = crm_manager.status_info(lead_id).get('name')
                if lead_status_str:
                    logger.info("Lead status: %s", lead_status_str)
                else:
                    lead_status_str = "Unknown"
            except Exception as e:
                logger.error("Error fetching lead status: %s", e)
                raise

            try:
                logger.info("Start save data")
                db_data = hook_decod.table_map(lead_status_str)
                json_saved_data = save_to_database(db_data)
                logger.info("Data saved")
            except Exception as e:
                logger.error("Data wrong: %s", e)
                raise

            audio_manager = AudioManager()
            try:
                if audio_url is not None:
                    audio_path = audio_manager.download(audio_url, audio_filename, json_saved_data["manager_id"])
                    logger.info("Audio download: %s", audio_path)

                    transcript_text = transcriptions(audio_file_mp3_path=str(audio_path))
                    logger.info("Transcription: %s", transcript_text)

                    audio_manager.delete(audio_path)
                else:
                    logger.info("Audio url is not exist")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise

            try:
                logger.info("Start Assistant")
                assistant_start(
                    transcrip_text=transcript_text,
                    crm_data_json=json_saved_data,
                    crm_manager=crm_manager
                )
                logger.info("Assistant analyzed data")
            except Exception as e:
                logger.error("Error saving data or running assistant: %s", e)
                raise

            logger.info("Data processed successfully")
            return "Data processed successfully"

    except Exception as e:
        logger.error("Error processing webhook data: %s", e)
        raise
