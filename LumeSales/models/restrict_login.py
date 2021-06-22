import logging

import pytz

from odoo import api, models, fields, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)

# class RestrictLogin(models.Model):
#     _inherit = 'res.users'

#     logged_in = fields.Boolean('Logged In')

#     @classmethod
#     def _login(cls, db, login, password, user_agent_env):
#         if not password:
#             raise AccessDenied()
#         ip = request.httprequest.environ['REMOTE_ADDR'] if request else 'n/a'
#         try:
#             with cls.pool.cursor() as cr:
#                 self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
#                 with self._assert_can_auth():
#                     user = self.search(self._get_login_domain(login), order=self._get_login_order(), limit=1)
#                     if not user:
#                         raise AccessDenied()
#                     user = user.with_user(user)
#                     user._check_credentials(password, user_agent_env)
#                     # Kick if user is already logged in
#                     if user.logged_in:
#                         raise AccessDenied("You are already logged in!")
#                     tz = request.httprequest.cookies.get('tz') if request else None
#                     if tz in pytz.all_timezones and (not user.tz or not user.login_date):
#                         # first login or missing tz -> set tz to browser tz
#                         user.tz = tz
#                     user._update_last_login()
#                     user.logged_in = True # Set user logged in
#         except AccessDenied:
#             _logger.info("Login failed for db:%s login:%s from %s", db, login, ip)
#             raise

#         _logger.info("Login successful for db:%s login:%s from %s", db, login, ip)

#         return user.id