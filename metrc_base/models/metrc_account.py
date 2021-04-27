# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import os
import sys
import json
import base64
import zipfile
import logging
import requests
import traceback

from pathlib import Path
from psycopg2 import OperationalError
from requests.auth import HTTPBasicAuth
from datetime import datetime


from odoo import api, fields, models, registry, _
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
from odoo.tools import exception_to_unicode, pycompat
from odoo.tools.osutil import tempdir

_logger = logging.getLogger(__name__)

_region_url_mapping = {
    'CA': {
        'production': 'https://api-ca.metrc.com',
        'sandbox': 'https://sandbox-api-ca.metrc.com'
    },
    'MI': {
        'production': 'https://api-mi.metrc.com',
        'sandbox': 'https://sandbox-api-mi.metrc.com'
    }
}

REQUEST_TIMEOUT = 180

KNOWN_ERROR_CODES = {
    401: {
        'message': _('Unauthorized ! Invalid or no authentication provided.'),
        'retry': False
    },
    403: {
        'message': _('Forbidden ! The authenticated user does not have access to the requested resource.'),
        'retry': False
    },
    404: {
        'message': _('Not Found ! The requested resource could not be found (incorrect or invalid URI).'),
        'retry': False
    },
    429: {
        'message': _('Too Many Requests ! The limit of API calls allowed has been exceeded. Please pace the usage rate of the API more apart.'),
        'retry': True
    },
    500: {
        'message': _('Internal Server Error ! An error has occurred while executing your request. The error message is typically included in the body of the response.'),
        'retry': False
    },
    503: {
        'message': _('SERVICE UNAVAILABLE! This could be a METRC api outage. Please try after some time.'),
        'retry': True
    },
    504: {
        'message': _('GATEWAY TIMEOUT! This could be a METRC api outage. Please try after some time.'),
        'retry': True
    }
}


class MetrcAccount(models.Model):

    _name = 'metrc.account'
    _description = 'Metrc Accounts'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, index=True)
    active = fields.Boolean(string='Active', default=True)
    software_api_key = fields.Char(string='Vendor\'s API Key', required=True, copy=False)
    user_api_key = fields.Char(string='User\'s API Key', required=True, copy=False)
    prod_environment = fields.Boolean(string='Mode',
                              help='Set to production mode if account api key\'s are certified '
                                    'for running in production, else use test mode for testing and demo.')
    api_version = fields.Selection(
        selection=[('v1', 'v1')], string='API Version', required=True, default='v1')
    region = fields.Selection(
        selection=[('CA', 'CA'), ('MI', 'MI')], string='API Region', default='CA', required=True)
    service_account = fields.Boolean(string='Service Account', copy=False)
    related_user = fields.Reference(selection=[
                                        ('res.users', 'User'),
                                        ('res.partner', 'Contact'),
                                    ],
                                    string='Account User', copy=False,
                                    compute='_compute_related_user')
    debug_logging = fields.Boolean('Debug logging', help='Log requests in order to ease debugging')
    logging_ids = fields.One2many(
        comodel_name='ir.logging', inverse_name='account_id', string='Loggins')

    _sql_constraints = [
        ('metrc_account_unique_apikey', 'unique (software_api_key, user_api_key, api_version)', 'The Metrc API keys pair (Vendor API Key and ) must be unique !'),
    ]

    def _compute_related_user(self):
        for account in self:
            user = self.env['res.users'].search([('metrc_account_id', '=', account.id)], limit=1)
            account.related_user = ('res.users,%d' % (user.id)) if user else False

    def toggle_service_account(self):
        for macc in self:
            macc.service_account = not macc.service_account

    def toggle_prod_environment(self):
        for macc in self:
            macc.prod_environment = not macc.prod_environment

    def toggle_debug(self):
        for macc in self:
            macc.debug_logging = not macc.debug_logging

    def _get_auth_header(self):
        self.ensure_one()
        return HTTPBasicAuth(self.software_api_key, self.user_api_key)

    def open_account_logs(self):
        action = self.env.ref('base.ir_logging_all_act').read()[0]
        action.update({
            'domain':  [('account_id', 'in', self.ids)]
        })
        return action

    def log_exception(self, level='error', func='/'):
        with self.pool.cursor() as cr:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            filename = exc_traceback.tb_frame.f_code.co_filename
            lineno = exc_traceback.tb_lineno
            name = exc_traceback.tb_frame.f_code.co_name,
            stack = traceback.format_exc()
            stack_msg = '%s\n\ncontext: %s\n' % (stack, str(self._context))
            cr.execute('''
                INSERT INTO
                    ir_logging(create_date, create_uid, type, dbname, name, level, message, path, line, func, account_id, active)
                VALUES
                (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (self.env.uid, 'server', self._cr.dbname, str(exc_type), level, stack_msg, filename, lineno, name, self.id, '1'))
        return True

    def log_message(self, name, message, level='info', path='/', line='0', func='/'):
        # Usually when we are performing a call to the third party provider to either refresh/fetch transaction/add user, etc,
        # the call can fail and we raise an error. We also want the error message to be logged in the object in the case the call
        # is done by a cron. This is why we are using a separate cursor to write the information on the chatter. Otherwise due to
        # the raise(), the transaction would rollback and nothing would be posted on the chatter.
        with self.pool.cursor() as cr:
            cr.execute('''
                INSERT INTO
                    ir_logging(create_date, create_uid, type, dbname, name, level, message, path, line, func, account_id, active)
                VALUES
                (NOW() at time zone 'UTC', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (self.env.uid, 'server', self._cr.dbname, name, level, message, path, line, func, self.id, '1'))
        return True

    def test_metrc_connection(self):
        self.ensure_one()
        resp = self.fetch('get', '/unitsofmeasure/v1/active')
        if resp:
            raise UserError(_('Connection Test Succeeded! Everything seems properly set up !'))
        else:
            raise ValidationError(_('Connection Test Failed! Check your network and account credentials !'))

    def fetch(self, http_method, service_endpoint, header=None, params=None, data=None, raise_for_error=True, timeout=180):
        retries = 0
        while True:
            if params is None:
                params = {}
            if data is None:
                data = {}
            if not service_endpoint:
                return False
            if header is None:
                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            if self.prod_environment:
                base_url = _region_url_mapping[self.region]['production']
            else:
                base_url = _region_url_mapping[self.region]['sandbox']

            service_url = '{}{}'.format(base_url, service_endpoint)
            func = '{}:{}'.format(http_method, service_endpoint)
            basic_auth = self._get_auth_header()
            request_message = '''
    HTTP Method : %s\n
    Service URL : %s\n
    Request params : \n%s\n
    Request Data   : \n%s\n
    context   : \n%s\n''' % (http_method, service_url, str(params), str(data), str(self._context))
            level = 'info'
            resp = None
            try:
                if self.debug_logging:
                    self.log_message('metrc.request', request_message, level=level, path=http_method, func=func)
                session = requests.Session()
                resp = session.request(http_method, service_url, headers=headers, auth=basic_auth, params=params, data=json.dumps(data), timeout=timeout)
                _logger.info('{} {} {} - {resp_time:.3f} Attempt: {attempt}'.format(http_method, resp.url,
                                                                             resp.status_code,
                                                                             resp_time=resp.elapsed.total_seconds(),
                                                                             attempt=retries))
            except requests.exceptions.Timeout as ex:
                self.log_exception(func=func)
                raise UserError(_('Timeout: the server did not reply within {}s'.format(timeout)))
            except Exception as ex:
                _logger.info('Exception: {}'.format(ex))
                self.log_exception(func=func)
                if resp:
                    resp.raise_for_status()
                else:
                    raise ex
            # This part for clean error handling and logging.
            # https://api-ca.metrc.com/Documentation#getting-started_server_responses
            if resp.status_code != 200:
                level = 'warning'
                message = 'Metrc Error'
                if params.get('licenseNumber'):
                    message += ' (facility license used : {})'.format(params['licenseNumber'])
                message += ' : \n\n'
                if resp.status_code == 503:
                    message += KNOWN_ERROR_CODES[resp.status_code]['message']
                    raise UserError(message)
                if resp.status_code == 400:
                    json_resp = resp.json()
                    if type(json_resp) in (list, tuple):
                        message += '.\n'.join([json_line.get('message') for json_line in json_resp])
                    else:
                        message += json_resp.get('Message')
                elif resp.status_code in KNOWN_ERROR_CODES:
                    if KNOWN_ERROR_CODES[resp.status_code]['retry']:
                        retries = retries + 1
                        if retries <= 3:
                            time.sleep(retries * 1.5)
                            continue
                    message += KNOWN_ERROR_CODES[resp.status_code]['message']
                    message += " Attempted {} retries.".format(retries)
                else:
                    message = 'Unexpected error ! please report this to your administrator.'
                    level = 'error'
                if raise_for_error:
                    raise UserError(message)
                else:
                    request_message += '\n Error : \n%s\n' % (message)
                    self.log_message(resp.status_code, request_message, level=level, path=http_method, func=func)
            try:
                return_data = resp.json()
            except Exception as ex:
                self.log_exception(func=func)
                return_data = {}
            if self.debug_logging:
                request_message += '\nRequest response : \n%s\n' % (str(return_data.copy()))
                self.log_message('metrc.response(200)', request_message, level=level, path=http_method, func=func)
            return return_data
