import logging
from functools import wraps
from typing import Optional

from flask import Response

from api.webhook.functions.database_orm import save_analyse_data_to_database
from models import Manager

logger = logging.getLogger(__name__)


def has_permission(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        manager_id = kwargs.get("manager_id")
        if manager_id is None and len(args) > 2:
            manager_id = args[2]

        if manager_id is None:
            logger.error(
                "Manager ID is missing",
                extra={
                    "status_code": "400",
                    "status_message": "Missing manager ID",
                    "operation_type": "PERMISSION",
                    "service": "FLASK",
                },
            )
            return Response("Manager ID is required.", 400)

        if not check_user_permission(manager_id):
            logger.warning(
                f"Manager {manager_id} has no permissions",
                extra={
                    "status_code": "403",
                    "status_message": "No permission",
                    "operation_type": "PERMISSION",
                    "service": "FLASK",
                },
            )
            return Response("Manager does not have permission to analyze.", 403)

        logger.info(
            f"Permission granted for manager {manager_id}",
            extra={
                "status_code": "200",
                "status_message": "Permission granted",
                "operation_type": "PERMISSION",
                "service": "FLASK",
            },
        )

        return func(self, *args, **kwargs)

    return wrapper


def check_user_permission(manager_id: Optional[int]) -> bool:
    try:
        manager_permission = (
            Manager.query.with_entities(Manager.is_permissions)
            .filter_by(id=manager_id)
            .scalar()
        )
        return bool(manager_permission)
    except Exception:
        logger.error(
            f"Error checking permission for manager {manager_id}",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "Permission check error",
                "operation_type": "PERMISSION",
                "service": "FLASK",
            },
        )
        return False
