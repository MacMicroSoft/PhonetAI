import logging
from flask_admin.contrib.sqla import ModelView
from flask import request, redirect, url_for
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import Select2Widget
from flask_admin.model import InlineFormAdmin
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.orm import scoped_session, Session
from wtforms import BooleanField, SelectField
from database import SessionLocal

from api.openai.trancription import AssistanceHandlerOpenAI, client
from models import Assistant, db, Prompts


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class UserAdminView(SecureModelView):
    column_list = ('id', 'username')


class IntegrationsAdminView(SecureModelView):
    column_list = ('id', 'subdomain', 'link')
    column_searchable_list = ('subdomain', 'link')
    form_columns = ('subdomain', 'link')


class ManagerAdminView(SecureModelView):
    column_list = ('id', 'crm_user_id', 'username', 'type', 'is_permissions')
    column_searchable_list = ('username', 'crm_user_id')
    form_columns = ('crm_user_id', 'username', 'type', 'is_permissions')


class LeadsAdminView(SecureModelView):
    column_list = (
        'id', 'owner_id', 'account_id', 'element_id', 'element_type', 'manager_id', 'integration_id', 'text_message',
        'timestamp_x', 'created_at', 'updated_at', 'lead_status')
    column_searchable_list = ('owner_id', 'text_message', 'manager.username')
    form_columns = (
        'owner_id', 'account_id', 'element_id', 'element_type', 'manager_id', 'integration_id', 'text_message')
    column_filters = ('lead_status',)


class PhonetAdminView(SecureModelView):
    column_list = ('id', 'unique_uuid', 'audio_mp3', 'phone_number', 'duration', 'call_status', 'call_result')
    column_searchable_list = ('phone_number', 'call_result')
    form_columns = ('audio_mp3', 'phone_number', 'duration', 'call_status', 'call_result')


class AnalysesAdminView(ModelView):
    column_list = ('id', 'lead_element_id', 'audio_text', 'analysed_text', 'is_analysed', 'created_at')
    column_labels = {'lead_element_id': 'Lead Element ID'}
    column_searchable_list = ('audio_text', 'analysed_text')
    form_columns = ('lead_id', 'audio_text', 'analysed_text', 'is_analysed')

    def _lead_element_id_formatter(self, context, model, name):
        print(model.lead)
        return model.lead


class PhonetLeadsAdminView(SecureModelView):
    column_list = ('id', 'phonet_id', 'leads_id', 'last_update')
    column_searchable_list = ('phonet_id', 'leads_id')
    form_columns = ('phonet_id', 'leads_id', 'last_update')


# class PromptsAdminView(InlineFormAdmin):
#     form_columns = ["prompt_type", "content", "is_active"]
#     form_extra_fields = {
#         'is_active': BooleanField('Active', default=True)
#     }
#
#
class AssistantAdminView(ModelView):
    column_list = ["id", "assistant_name", "model", "description", "message_prompt", "is_active"]
    form_columns = ["assistant_name", "model", "description", "message_prompt", "is_active"]
    form_overrides = {"is_active": BooleanField}  # Використовуємо BooleanField для is_active#

    def on_model_change(self, form, model, is_created):
        try:
            if is_created:
                handler = AssistanceHandlerOpenAI(
                    assistant=None,
                    instructions=None,
                    message=None
                )
                assistant = handler.create_assistant(
                    name=model.assistant_name,
                    desc=model.description,
                    model=model.model
                )
                if not assistant:
                    raise ValueError("OpenAI Assistant creation failed")
                model.assistant_id = assistant.id
            else:
                if model.assistant_id:
                    handler = AssistanceHandlerOpenAI(
                        model.assistant_id,
                        instructions=None,
                        message=None
                    )
                    success = handler.update_assistant(
                        assistant_id=model.assistant_id,
                        desc=model.description,
                        name=model.assistant_name,
                        model=model.model
                    )
                    if not success:
                        logging.warning("OpenAI update failed")
        except Exception as e:
            logging.error(f"Assistant Sync Error: {str(e)}")
            raise
        finally:
            super().on_model_change(form, model, is_created)

    def on_model_delete(self, model):
        if model.assistant_id:
            handler = AssistanceHandlerOpenAI(
                model.assistant_id,
                instructions=None,
                message=None,
            )
            if not handler.delete_assistant(
                    assistant_id=model.assistant_id,
            ):
                logging.error(f"Failed to delete OpenAI assistant {model.assistant_id}")


class PromptsAdmin(ModelView):
    column_list = ["assistant_id", "prompt_type", "content", "is_active"]

    form_extra_fields = {
        "assistant": SelectField(
            "Assistant",
            coerce=int,  # Convert selected assistant to integer
            widget=Select2Widget()  # Use a select2 widget for better UI
        ),
    }

    def on_form_prefill(self, form, id):
        """Called when editing an existing record (NOT on create)."""
        print("on_form_prefill called!")
        with db.session() as session:
            assistants = session.query(Assistant).filter_by(is_active=True).all()
            print(f"Active assistants: {assistants}")
            form.assistant.choices = [(a.id, a.assistant_name) for a in assistants]

    def create_form(self, obj=None):
        """Called when creating a new record (different from on_form_prefill)."""
        form = super(PromptsAdmin, self).create_form(obj)
        with db.session() as session:
            assistants = session.query(Assistant).filter_by(is_active=True).all()
            print(f"Active assistants for creation: {assistants}")
            form.assistant.choices = [(a.id, a.assistant_name) for a in assistants]
        return form

    def on_model_change(self, form, model, is_created):
        """Ensure valid assistant_id is assigned on model change."""
        print("on_model_change called!")
        if not form.assistant.data:
            raise ValueError("You must select an assistant.")

        # Set the assistant_id to the selected assistant's id
        assistant_id = form.assistant.data
        model.assistant_id = assistant_id

        print(f"Assigned assistant_id {assistant_id} to model.")

    def __init__(self, *args, **kwargs):
        super(PromptsAdmin, self).__init__(*args, **kwargs)
