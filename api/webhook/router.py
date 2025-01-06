from flask import Blueprint, Response, request
import logging

logger = logging.getLogger(__name__)

hook_bp = Blueprint(
    'hook_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@hook_bp.route('/test/', methods=['POST'])
def webhook_from_CRM():
    try:
        if request.method == 'POST':
            data = request.data
            print(dir(request))
            print(data)
            # parse_hood_data(data)
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
                "status_message": str(e),
                "operation_type": "WEBHOOK",
                "service": "FLASK",
                "extra": {},
            },
        )
        return Response("Error processing data", status=400)
