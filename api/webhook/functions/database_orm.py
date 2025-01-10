import logging
from sqlalchemy import select
from database import SessionLocal
from models import *
import logging
from sqlalchemy import select
from database import SessionLocal
from models import *
import logging

logger = logging.getLogger(__name__)


def save_to_database(data: dict) -> None:

    logger.info(
        "Start decoding data",
        extra={
            "status_code": "100",
            "status_message": "DATA",
            "operation_type": "WEBHOOK",
            "service": "FLASK",
        },
    )

    db = SessionLocal()
    try:
        integration_data = data.get("Integrations")
        integration = None
        if integration_data:
            stmt = select(Integrations).filter_by(subdomain=integration_data["subdomain"])
            integration = db.execute(stmt).scalars().first()
            if not integration:
                integration = Integrations(**integration_data)
                db.add(integration)
                db.commit()
        manager_data = data.get("Manager")
        manager = None
        if manager_data:
            stmt = select(Manager).filter_by(crm_user_id=manager_data["crm_user_id"])
            manager = db.execute(stmt).scalars().first()
            if not manager:
                manager = Manager(**manager_data)
                db.add(manager)
                db.commit()

        leads_data = data.get("Leads")
        leads = None
        if leads_data:
            if not manager:
                raise ValueError("Manager is required but not found")
            if not integration:
                raise ValueError("Integration is required but not found")

            leads_data["manager_id"] = manager.id
            leads_data["integration_id"] = integration.id

            leads = Leads(**leads_data)
            db.add(leads)
            db.commit()

        phonet_data = data.get("Phonet")
        if phonet_data is not None:
            if phonet_data:
                phonet = Phonet(**phonet_data)
                db.add(phonet)
                db.commit()

            phonet_leads_data = data.get("PhonetLeads")
            if phonet_leads_data:
                if not phonet:
                    raise ValueError("Phonet is required but not found")
                if not leads:
                    raise ValueError("Leads is required but not found")

                phonet_leads_data["phonet_id"] = phonet.id
                phonet_leads_data["leads_id"] = leads.id

                phonet_leads = PhonetLeads(**phonet_leads_data)
                db.add(phonet_leads)

            db.commit()

        logger.info(
            "Successfully saved data to database",
            extra={
                "status_code": "100",
                "status_message": "DATA",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

    except Exception as e:
        logger.info(
            "Error saving to database",
            extra={
                "status_code": "500",
                "status_message": "SERVER",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
                "extra": {f"Error saving to database {e}"},
            },
        )
    finally:
        db.close()
