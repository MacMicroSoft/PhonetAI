from flask_admin.contrib.sqla import ModelView
from flask import request, redirect, url_for
from flask_admin import BaseView, expose
from flask_login import current_user


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
