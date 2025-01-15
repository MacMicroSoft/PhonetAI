import hashlib
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Blueprint, Response, request
import logging
import redis

from sqlalchemy import select
from database import SessionLocal
from api.webhook.functions.database_orm import save_to_database
from api.webhook.functions.source import HookDecoder
from models import Integrations, Leads

logger = logging.getLogger(__name__)
load_dotenv()
hook_bp = Blueprint('hook_bp', __name__, template_folder='templates', static_folder='static')

redis_client = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))


@hook_bp.route('/como/crm/', methods=['POST'])
def webhook_from_CRM():
    logger.info('Received webhook from CRM')
    logger.info(f'Request data: {request.data}')
    logger.info(f'Type of request data: {type(request.data)}')

    try:
        if request.method == 'POST':
            data = request.data
            hash_data = hashlib.sha256(data).hexdigest()
            REDIS_EXPIRE_TIME = 1800

            if redis_client.exists(hash_data):
                return Response("Duplicate data received, ignoring.", status=200)

            redis_client.set(hash_data, 1, ex=REDIS_EXPIRE_TIME)

            hook_decod = HookDecoder()
            hook_decod.webhook_decoder(raw_data=data)
            db_data = hook_decod.table_map()
            save_to_database(db_data)

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
    if request.method == 'GET':
        query = db.query(Leads).all()

        data = [
            {key: (
                getattr(element, key).isoformat() if isinstance(getattr(element, key), datetime) else getattr(element,
                                                                                                              key))
                for key in element.__dict__.keys() if key != '_sa_instance_state'}
            for element in query
        ]

        return Response(json.dumps({"data": data}, default=custom_serializer), status=200, mimetype='application/json')
