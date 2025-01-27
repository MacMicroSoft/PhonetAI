import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Integrations, Manager, Leads, Phonet, PhonetLeads, Analyses
from database import SessionLocal

logger = logging.getLogger(__name__)


def save_to_database(data: dict) -> dict:
    logger.info(
        "Start decoding data",
        extra={
            "status_code": "100",
            "status_message": "DATA",
            "operation_type": "WEBHOOK",
            "service": "FLASK",
        },
    )

    try:
        with SessionLocal() as db:
            integration_data = data.get("Integrations")
            integration = None

            if integration_data:
                integration = db.query(Integrations).filter_by(subdomain=integration_data["subdomain"]).first()
                if not integration:
                    integration = Integrations(**integration_data)
                    db.add(integration)
                    db.commit()

            manager_data = data.get("Manager")
            manager = None
            if manager_data:
                manager = db.query(Manager).filter_by(crm_user_id=manager_data["crm_user_id"]).first()
                if not manager:
                    manager = Manager(**manager_data)
                    db.add(manager)
                    db.commit()

            leads_data = data.get("Leads")
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
            if phonet_data:
                phonet = Phonet(**phonet_data)
                db.add(phonet)
                db.commit()

                phonet_leads_data = data.get("PhonetLeads")
                if phonet_leads_data:
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
            return {"manager_id": manager.id, "lead_id": leads.id, "phonet_id": phonet.id}

    except Exception as e:
        logger.error(
            "Error saving to database",
            extra={
                "status_code": "500",
                "status_message": "SERVER",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
                "error": str(e),
            },
        )


def save_analyse_data_to_database(data: dict) -> None:
    try:
        analyse_data = {
            "lead_id": data.get("lead_id"),
            "audio_text": data.get("audio_text"),
            "analysed_text": data.get("analysed_text"),
            "is_analysed": data.get("is_analysed")
        }

        with SessionLocal() as db:
            analysed_data = Analyses(**analyse_data)
            db.add(analysed_data)
            db.commit()

    except Exception as e:
        logger.error(f"Error saving analysed data: {e}")
        db.rollback()


def get_created_lead_id():
    pass
