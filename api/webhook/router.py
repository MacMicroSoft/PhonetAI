import os
import json
import redis
import hashlib
import logging
from flask import jsonify
from sqlalchemy import select
from datetime import datetime
from dotenv import load_dotenv

from api.openai.trancription import AssistanceHandlerOpenAI, assistant_start
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


ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjgzYWU4M2IxYmVhNzQ1NjIyZGVmZDRkMGUxYjA5YzY2NTRmOTg2ZDhmNmM5YmE1NjdhZjI2ZjNmNjMyZDljMGI0YThlMTUxYWM2ODQ3YTRkIn0.eyJhdWQiOiJiOGIyZWExOS1mZDRlLTQxYWUtYTIxMC1mOTU1ZDliYjQ3N2YiLCJqdGkiOiI4M2FlODNiMWJlYTc0NTYyMmRlZmQ0ZDBlMWIwOWM2NjU0Zjk4NmQ4ZjZjOWJhNTY3YWYyNmYzZjYzMmQ5YzBiNGE4ZTE1MWFjNjg0N2E0ZCIsImlhdCI6MTczNzE0MzQyMiwibmJmIjoxNzM3MTQzNDIyLCJleHAiOjE3MzcyNDQ4MDAsInN1YiI6IjY4MTc1MjIiLCJncmFudF90eXBlIjoiIiwiYWNjb3VudF9pZCI6Mjg2NzcwNTUsImJhc2VfZG9tYWluIjoia29tbW8uY29tIiwidmVyc2lvbiI6Miwic2NvcGVzIjpbInB1c2hfbm90aWZpY2F0aW9ucyIsImNybSIsIm5vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiYjhmOTVmMDAtODFlMS00Yzg1LWJhYTYtZWJmOWViNWZmOTJkIiwiYXBpX2RvbWFpbiI6ImFwaS1nLmtvbW1vLmNvbSJ9.Keu2KSPpdAb7SX_RgG3m9GK-HuUI6rP-DLL-hbGX13u99NKbpRvxfGgJQWFz7DmQKEFD2PZ_hHKMn-_c1flzYiLl-7Mc356rjUDAMVn9HsQXGuyNetGVjFwAxkoCXBDlNYUq3Mk_GcnxrrORFY1nyZeW5_qgY-8HGOYRIbeusHJOZ-_sPSOcUQEg8AlNrxmeVSPDuZhuAJ50-NavadW5-Ps5Tgy3oXFuYo2RWhP4DH3Ax2TtcUsOpwZYrStkIwfNF3beFbZRNMpCSh9Vh5015aV3fCTpgzEvOPTKNYiCnE8t4iPteLE0GlB_FhxHJ6FZ7RJDShmI2zKHAQK8vSxBrw"
#Спочатку так для теста потім треба буде в ApiCRMManager зробити автоматизовано отримання/оновлення токену


@hook_bp.route('/como/crm/', methods=['POST'])
def webhook_from_CRM():
    try:
        if request.method == 'POST':
            data = request.data
            logger.info(f"Get data as bytes: {str(data)}")

            hash_data = hashlib.sha256(data).hexdigest()

            # REDIS_EXPIRE_TIME = 1800

            # if redis_client.exists(hash_data):
            #     return Response("Duplicate data received, ignoring.", status=200)
            #
            # redis_client.set(hash_data, 1, ex=REDIS_EXPIRE_TIME)

            hook_decod = HookDecoder()
            hook_decod.webhook_decoder(raw_data=data)

            audio_filename, audio_url, lead_id, url_domain = hook_decod.integration_data()
            print(audio_filename, audio_url, lead_id, url_domain)
            print('\n')

            try:
                audio_manager: AudioManager = AudioManager()
                audio_path = audio_manager.download(audio_url, audio_filename)
                print(f"\nAудіо викачане успішно!\nPath: {audio_path}")

                audio_manager.delete(audio_path)
            except:
                print("\nПомилка з аудіо")

            try:
                crm_manager: ApiCRMManager = ApiCRMManager(url_domain, access_token=ACCESS_TOKEN)
                lead_status_str: str = crm_manager.status_info(lead_id).get('name')
                print(f"Cтатус Ліда: {lead_status_str}")
            except:
                print("\nПомилка в отриманні статусу ліда")

            db_data = hook_decod.table_map(lead_status_str)

            save_to_database(db_data)

            assistant_start(file_path="somepath")

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
    except Exception as e:
        logger.info(
            "Error processing data from webhook",
            extra={
                "status_code": "400",
                "status_message": "BAD REQUEST",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
                "extra": {str(e)},
            },
        )
        return Response("Error processing data", status=400)


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
