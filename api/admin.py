from flask_admin.contrib.sqla import ModelView
from flask import request, redirect, url_for
from flask_admin import BaseView, expose
from flask_login import current_user


class UserAdminView(ModelView):
    column_list = ('id', 'username', 'email')
    column_searchable_list = ('username', 'email')
    form_columns = ('username', 'email')
    column_filters = ('username',)


class IntegrationsAdminView(ModelView):
    column_list = ('id', 'subdomain', 'link')
    column_searchable_list = ('subdomain', 'link')
    form_columns = ('subdomain', 'link')


class ManagerAdminView(ModelView):
    column_list = ('id', 'crm_user_id', 'username', 'type', 'is_permissions')
    column_searchable_list = ('username', 'crm_user_id')
    form_columns = ('crm_user_id', 'username', 'type', 'is_permissions')


class LeadsAdminView(ModelView):
    column_list = (
        'id', 'owner_id', 'account_id', 'element_id', 'element_type', 'manager_id', 'integration_id', 'text_message',
        'timestamp_x', 'created_at', 'updated_at', 'lead_status')
    column_searchable_list = ('owner_id', 'text_message', 'manager.username')
    form_columns = (
        'owner_id', 'account_id', 'element_id', 'element_type', 'manager_id', 'integration_id', 'text_message')
    column_filters = ('lead_status',)


class PhonetAdminView(ModelView):
    column_list = ('id', 'unique_uuid', 'audio_mp3', 'phone_number', 'duration', 'call_status', 'call_result')
    column_searchable_list = ('phone_number', 'call_result')
    form_columns = ('audio_mp3', 'phone_number', 'duration', 'call_status', 'call_result')


class AnalysesAdminView(ModelView):
    column_list = ('id', 'lead_id', 'audio_text', 'analysed_text', 'is_analysed', 'created_at')
    column_searchable_list = ('audio_text', 'analysed_text')
    form_columns = ('lead_id', 'audio_text', 'analysed_text', 'is_analysed')


class PhonetLeadsAdminView(ModelView):
    column_list = ('id', 'phonet_id', 'leads_id', 'last_update')
    column_searchable_list = ('phonet_id', 'leads_id')
    form_columns = ('phonet_id', 'leads_id', 'last_update')
