import os
import json
import redis
import hashlib
import logging
from flask import jsonify
from sqlalchemy import select
from datetime import datetime
from dotenv import load_dotenv

from api.openai.trancription import assistant_start, transcriptions
from database import SessionLocal
from flask import Blueprint, Response, request
from api.webhook.functions.source import HookDecoder
from api.webhook.functions.database_orm import save_to_database
from api.webhook.functions.source import HookDecoder, ApiCRMManager, AudioManager
from models import Integrations, Leads, Manager, Phonet, PhonetLeads

logger = logging.getLogger(__name__)
load_dotenv()
hook_bp = Blueprint('hook_bp', __name__, template_folder='templates', static_folder='static')

# redis_client = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))


ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")


@hook_bp.route('/como/crm/', methods=['POST'])
def webhook_from_CRM():
    # try:
    if request.method == 'POST':
        data = request.get_data()
        logger.info(f"Get data as bytes: {str(data)}")
        print(data, "check_data")
        hash_data = hashlib.sha256(data).hexdigest()

        # REDIS_EXPIRE_TIME = 1800

        # if redis_client.exists(hash_data):
        #     return Response("Duplicate data received, ignoring.", status=200)
        #
        # redis_client.set(hash_data, 1, ex=REDIS_EXPIRE_TIME)

        hook_decod = HookDecoder()
        hook_decod.webhook_decoder(raw_data=data)

        audio_filename, audio_url, lead_id, url_domain = hook_decod.integration_data()
        print(audio_filename, audio_url, lead_id, url_domain, "///////")
        print('\n')

        try:
            crm_manager: ApiCRMManager = ApiCRMManager(url_domain, access_token=ACCESS_TOKEN)
            lead_status_str: str = crm_manager.status_info(lead_id).get('name')
            print(f"Cтатус Ліда: {lead_status_str}")
        except:
            print("\nПомилка в отриманні статусу ліда")

        # try:
        audio_manager: AudioManager = AudioManager()
        audio_path = audio_manager.download(audio_url, audio_filename)
        transcript_text = transcriptions(audio_file_mp3_path=audio_path)
        audio_manager.delete(audio_path)
        # except:
        #     print("\nПомилка з аудіо")

        db_data = hook_decod.table_map(lead_status_str)

        json_saved_data = save_to_database(db_data)

        assistant_start(transcrip_text=transcript_text, crm_data_json=json_saved_data, crm_manager=crm_manager)

        logger.info(
            "Successfully received data from webhook",
            extra={
                "status_code": "100",
                "status_message": "DATA",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
                "extra": {},
            },
        )
        return Response("Data received successfully", status=200)
    # except Exception as e:
    #     logger.info(
    #         "Error processing data from webhook",
    #         extra={
    #             "status_code": "400",
    #             "status_message": "BAD REQUEST",
    #             "operation_type": "WEBHOOK",
    #             "service": "FLASK",
    #             "extra": {str(e)},
    #         },
    #     )
    #     return Response("Error processing data", status=400)


def custom_serializer(obj):
    """Serializer for objects that are not supported by JSON."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


@hook_bp.route('/como/crm/info/', methods=['GET'])
def webhook_info():
    db = SessionLocal()
    try:
        if request.method == "GET":
            leads = db.query(Leads).all()
            managers = db.query(Manager).all()
            integrations = db.query(Integrations).all()
            phonet = db.query(Phonet).all()
            phonet_leads = db.query(PhonetLeads).all()

            leads_list = [
                {key: value for key, value in lead.__dict__.items() if not key.startswith("_")}
                for lead in leads
            ]
            managers_list = [
                {key: value for key, value in manager.__dict__.items() if not key.startswith("_")}
                for manager in managers
            ]
            integrations_list = [
                {key: value for key, value in integration.__dict__.items() if not key.startswith("_")}
                for integration in integrations
            ]
            phonet_list = [
                {key: value for key, value in phone.__dict__.items() if not key.startswith("_")}
                for phone in phonet
            ]
            phonet_leads_list = [
                {key: value for key, value in phonet_lead.__dict__.items() if not key.startswith("_")}
                for phonet_lead in phonet_leads
            ]

            response = {
                "leads": leads_list,
                "managers": managers_list,
                "integrations": integrations_list,
                "phonet": phonet_list,
                "phonet_leads": phonet_leads_list,
            }

            return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()