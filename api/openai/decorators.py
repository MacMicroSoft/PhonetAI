from typing import Optional

from flask import abort, Response

from api.webhook.functions.database_orm import save_analyse_data_to_database
from models import Manager
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def has_permission(func):
    @wraps(func)
    def wrapper(crm_data_json, transcrip_text: str, *args, **kwargs):
        manager_id = crm_data_json["manager_id"]

        if not check_user_permission(manager_id):
            data = {
                "lead_id": crm_data_json["lead_id"],
                "audio_text": transcrip_text,
                "analysed_text": None,
                "is_analysed": False,
            }
            save_analyse_data_to_database(data=data)

            logger.info("The manager has not permissions")
            return Response("The manager has not permissions", status=403)
        return func(transcrip_text, crm_data_json, *args, **kwargs)

    return wrapper


def check_user_permission(manager_id: Optional[int]) -> bool:
    manager_permission = (
        Manager.query.with_entities(Manager.is_permissions)
        .filter_by(id=manager_id)
        .scalar()
    )

    if not manager_permission:
        logger.info("The manager has no permissions.")
        return False
    return True
