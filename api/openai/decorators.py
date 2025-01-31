from typing import Optional

from flask import abort, Response

from api.webhook.functions.database_orm import save_analyse_data_to_database
from models import Manager
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def has_permission(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        manager_id = kwargs.get("manager_id")
        if manager_id is None and len(args) > 2:
            manager_id = args[2]

        if manager_id is None:
            logger.error("Manager ID is missing.")
            return Response("Manager ID is required.", 400)

        if not check_user_permission(manager_id):
            logger.info("The manager has no permissions.")
            return Response("Manager does not have permission to analyze.", 403)

        return func(self, *args, **kwargs)

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
