import logging

from sqlalchemy.orm import Session
from models import Integrations, Manager, Leads, Phonet, PhonetLeads, Analyzes
from database import SessionLocal

logger = logging.getLogger(__name__)


def save_to_database(data: dict) -> dict:
    logger.info(
        "Start saving incoming data to database",
        extra={
            "status_code": "100",
            "status_message": "Start DB save",
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
                    logger.error(
                        "Missing manager while saving lead",
                        extra={
                            "status_code": "400",
                            "status_message": "Manager missing",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )
                    raise ValueError("Manager is required but not found")

                if not integration:
                    logger.error(
                        "Missing integration while saving lead",
                        extra={
                            "status_code": "400",
                            "status_message": "Integration missing",
                            "operation_type": "WEBHOOK",
                            "service": "FLASK",
                        },
                    )
                    raise ValueError("Integration is required but not found")

                leads_data["manager_id"] = manager.id
                leads_data["integration_id"] = integration.id
                leads = Leads(**leads_data)
                db.add(leads)
                db.commit()
            else:
                leads = None

            phonet_data = data.get("Phonet")
            if phonet_data:
                phonet = Phonet(**phonet_data)
                db.add(phonet)
                db.commit()

                phonet_leads_data = data.get("PhonetLeads")
                if phonet_leads_data:
                    if not leads:
                        logger.error(
                            "Missing lead while saving PhonetLeads",
                            extra={
                                "status_code": "400",
                                "status_message": "Leads missing",
                                "operation_type": "WEBHOOK",
                                "service": "FLASK",
                            },
                        )
                        raise ValueError("Leads is required but not found")

                    phonet_leads_data["phonet_id"] = phonet.id
                    phonet_leads_data["leads_id"] = leads.id
                    phonet_leads = PhonetLeads(**phonet_leads_data)
                    db.add(phonet_leads)
                    db.commit()
            else:
                phonet = None

            logger.info(
                "Data saved to database successfully",
                extra={
                    "status_code": "200",
                    "status_message": "DB save complete",
                    "operation_type": "WEBHOOK",
                    "service": "FLASK",
                },
            )

            return {
                "manager_id": manager.id if manager else None,
                "lead_id": leads.id if leads else None,
                "lead_element_id": leads.element_id if leads else None,
                "phonet_id": phonet.id if phonet else None,
            }

    except Exception as e:
        logger.error(
            "Exception during saving to database",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "Database save error",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )
        raise


def save_analyse_data_to_database(data: dict) -> None:
    logger.info(
        "Start saving analysis data",
        extra={
            "status_code": "100",
            "status_message": "Start analysis DB save",
            "operation_type": "WEBHOOK",
            "service": "FLASK",
        },
    )

    try:
        analyse_data = {
            "lead_id": data.get("lead_id"),
            "audio_text": data.get("audio_text"),
            "analysed_text": data.get("analysed_text"),
            "is_analysed": data.get("is_analysed"),
        }

        with SessionLocal() as db:
            analysed_data = Analyzes(**analyse_data)
            db.add(analysed_data)
            db.commit()

        logger.info(
            "Analysis data saved successfully",
            extra={
                "status_code": "200",
                "status_message": "Analysis data saved",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )

    except Exception:
        logger.error(
            "Error saving analysed data",
            exc_info=True,
            extra={
                "status_code": "500",
                "status_message": "Analysis DB save error",
                "operation_type": "WEBHOOK",
                "service": "FLASK",
            },
        )
        raise


def get_created_lead_id():
    pass
