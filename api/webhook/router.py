from flask import Blueprint, Response, request
import logging

from .functions.database_orm import save_to_database
from api.webhook.functions.source import *

logger = logging.getLogger(__name__)

hook_bp = Blueprint(
    'hook_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@hook_bp.route('/como/crm/', methods=['POST'])
def webhook_from_CRM():
    print(request)
    try:
        if request.method == 'POST':
            data = request.data
            hook_decod = HookDecoder()
            hook_decod.webhook_decoder(raw_data=data)
            db_data: dict = hook_decod.table_map()  #Дані для бази даних розбиті на таблиці
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
        logger.error(
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