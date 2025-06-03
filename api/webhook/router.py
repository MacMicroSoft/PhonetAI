import hashlib
import logging
import os

from dotenv import load_dotenv
from flask import Blueprint, Response, request

from api.openai.trancription import assistant_start, transcriptions
from api.webhook.functions.database_orm import save_to_database
from api.webhook.functions.source import AudioManager, ApiCRMManager, HookDecoder
from redis_config import redis_client
from celery_settings import celery

logger = logging.getLogger(__name__)

load_dotenv()
webhook_route = Blueprint('webhook', __name__)


def get_app():
    from app import app
    return app


@webhook_route.route('/como/crm/', methods=['POST'])
def webhook_from_CRM():
    try:
        if request.method != 'POST':
            logger.warning(
                "Invalid HTTP method",
                extra={
                    "status_code": "400",
                    "status_message": "Invalid HTTP method",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )
            return Response("Only POST method is allowed.", status=405)

        data = request.get_data()
        hash_data = hashlib.sha256(data).hexdigest()

        if redis_client.exists(hash_data):
            logger.info(
                "Duplicate webhook detected",
                extra={
                    "status_code": "400",
                    "status_message": "Duplicate webhook",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )
            return Response("Duplicate data received, ignoring.", status=200)

        redis_client.set(hash_data, 1, ex=180)

        logger.info(
            "Webhook received and accepted",
            extra={
                "status_code": "201",
                "status_message": "Webhook accepted",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

        process_webhook_data.delay(data)
        return Response("Webhook received and processing started", status=200)

    except Exception:
        logger.error(
            "Unhandled exception in webhook_from_CRM",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "Webhook endpoint failure",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )
        return Response("Internal server error", status=500)


@celery.task
def process_webhook_data(data):
    try:
        app = get_app()
        with app.app_context():
            logger.info(
                "Start decoding webhook data",
                extra={
                    "status_code": "100",
                    "status_message": "Decoding webhook data",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )

            hook_decod = HookDecoder()
            hook_decod.webhook_decoder(raw_data=data)
            audio_filename, audio_url, lead_id, url_domain = hook_decod.integration_data()

            logger.info(
                "Webhook data decoded successfully",
                extra={
                    "status_code": "200",
                    "status_message": "Decoded data",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )

            try:
                crm_manager = ApiCRMManager(url_domain, access_token=os.getenv("ACCESS_TOKEN"))
                lead_status_str = crm_manager.status_info(lead_id).get("name") or "Unknown"

                logger.info(
                    "Fetched lead status from CRM",
                    extra={
                        "status_code": "200",
                        "status_message": "Lead status fetched",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
            except Exception:
                logger.error(
                    "Failed to fetch lead status",
                    exc_info=True,
                    extra={
                        "status_code": "500",
                        "status_message": "CRM status fetch failed",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
                raise

            try:
                logger.info(
                    "Saving data to database",
                    extra={
                        "status_code": "100",
                        "status_message": "Saving data",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )

                db_data = hook_decod.table_map(lead_status_str)
                json_saved_data = save_to_database(db_data)

                logger.info(
                    "Data saved to database",
                    extra={
                        "status_code": "200",
                        "status_message": "Data saved",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
            except Exception:
                logger.error(
                    "Failed to save data to DB",
                    exc_info=True,
                    extra={
                        "status_code": "500",
                        "status_message": "DB save error",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
                raise

            transcript_text = ""
            audio_manager = AudioManager()

            try:
                if audio_url:
                    logger.info(
                        "Downloading audio file",
                        extra={
                            "status_code": "100",
                            "status_message": "Downloading audio",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )

                    audio_path = audio_manager.download(audio_url, audio_filename, json_saved_data["manager_id"])

                    logger.info(
                        "Audio downloaded, starting transcription",
                        extra={
                            "status_code": "100",
                            "status_message": "Transcription started",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )

                    transcript_text = transcriptions(audio_file_mp3_path=str(audio_path))

                    logger.info(
                        "Transcription completed",
                        extra={
                            "status_code": "200",
                            "status_message": "Audio transcribed",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )

                    audio_manager.delete(audio_path)

                    logger.info(
                        "Audio file deleted after processing",
                        extra={
                            "status_code": "200",
                            "status_message": "Audio cleanup",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )
                else:
                    logger.warning(
                        "No audio URL provided",
                        extra={
                            "status_code": "400",
                            "status_message": "Missing audio URL",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )
            except Exception:
                logger.error(
                    "Audio processing or transcription failed",
                    exc_info=True,
                    extra={
                        "status_code": "500",
                        "status_message": "Audio processing error",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
                raise

            try:
                logger.info(
                    "Running assistant analysis",
                    extra={
                        "status_code": "100",
                        "status_message": "Assistant started",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )

                assistant_start(
                    transcrip_text=transcript_text,
                    crm_data_json=json_saved_data,
                    crm_manager=crm_manager,
                )

                logger.info(
                    "Assistant analysis completed",
                    extra={
                        "status_code": "200",
                        "status_message": "Assistant finished",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
            except Exception:
                logger.error(
                    "Assistant execution failed",
                    exc_info=True,
                    extra={
                        "status_code": "500",
                        "status_message": "Assistant error",
                        "operation_type": "WEBHOOK",
                        "service": "FLASK",
                    },
                )
                raise

            logger.info(
                "Webhook data processed successfully",
                extra={
                    "status_code": "200",
                    "status_message": "Webhook complete",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )

    except Exception:
        logger.error(
            "Unhandled exception in Celery task",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "Webhook processing failure",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )
        raise
