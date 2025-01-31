from flask_admin.contrib.sqla import ModelView
from flask import request, redirect, url_for
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import Select2Widget
from flask_login import current_user
from wtforms import BooleanField, SelectField
from database import SessionLocal

from api.openai.trancription import AssistanceHandlerOpenAI, client
from models import Assistant, db


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


class AnalysesAdminView(SecureModelView):
    column_list = ('id', 'lead_id', 'audio_text', 'analysed_text', 'is_analysed', 'created_at')
    column_searchable_list = ('audio_text', 'analysed_text')
    form_columns = ('lead_id', 'audio_text', 'analysed_text', 'is_analysed')


class PhonetLeadsAdminView(SecureModelView):
    column_list = ('id', 'phonet_id', 'leads_id', 'last_update')
    column_searchable_list = ('phonet_id', 'leads_id')
    form_columns = ('phonet_id', 'leads_id', 'last_update')


class AssistantAdminView(ModelView):
    column_list = ["assistant_name", "model", "description", "message_promt", "is_active"]
    form_columns = ["assistant_name", "model", "description", "message_promt", "is_active"]
    form_overrides = {"is_active": BooleanField}  # Використовуємо BooleanField для is_active

    def on_model_change(self, form, model, is_created):
        if is_created:
            print("Запис створено")
            openai_helper = AssistanceHandlerOpenAI(
                assistant=None,
                instructions=None,
                message=None,
            )
            assistant = openai_helper.create_assistant(
                name=model.assistant_name,
                desc=model.description,
                model=model.model
            )
            if assistant:
                model.assistant_id = assistant.id
        else:
            print("Запис оновлено")

        super().on_model_change(form, model, is_created)


class PromptsAdmin(ModelView):
    form_extra_fields = {
        "assistant": SelectField(
            "Assistant",
            choices=[],  # Заповнюється динамічно в `on_form_prefill`
            coerce=int,
            widget=Select2Widget()
        )
    }

    def on_form_prefill(self, form, id):
        """Викликається при редагуванні (НЕ при створенні!)"""
        print(" on_form_prefill викликано!")
        with db.session() as session:
            assistants = session.query(Assistant).filter_by(is_active=True).all()
            print(f" Отримані асистенти: {assistants}")
            form.assistant.choices = [(a.id, a.assistant_name) for a in assistants]

    def create_form(self, obj=None):
        """Цей метод потрібен для створення нових записів (на відміну від on_form_prefill)"""
        form = super(PromptsAdmin, self).create_form(obj)
        with db.session() as session:
            assistants = session.query(Assistant).filter_by(is_active=True).all()
            print(f" Отримані асистенти для створення: {assistants}")
            form.assistant.choices = [(a.id, a.assistant_name) for a in assistants]
        return form

    def __init__(self, *args, **kwargs):
        super(PromptsAdmin, self).__init__(*args, **kwargs)
