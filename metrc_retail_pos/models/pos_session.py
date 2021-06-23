# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, registry, _


class PosSession(models.Model):
    _inherit = 'pos.session'

    session_reported = fields.Boolean(compute='_compute_session_reported', string='Reported to Metrc?')
    need_to_report = fields.Boolean(compute='_compute_session_reported', string='Needs METRC Reporting?')

    @api.depends('order_ids', 'order_ids.metrc_retail_state')
    def _compute_session_reported(self):
        for session in self:
            session.session_reported = False
            session.need_to_report = False
            if session.order_ids and session.state == 'closed' and session.crm_team_id.metrc_retail_reporting and\
               any([p.is_metric_product for p in session.order_ids.mapped('lines').mapped('product_id')]):
                session.need_to_report = True
                if all([o.metrc_retail_state == 'Reported' for o in session.order_ids]):
                    session.session_reported = True

    def action_report_session(self):
        PosOrder = self.env['pos.order']
        PosOrder._cron_flag_retail_pos(session_ids=self.ids, automatic=False, raise_for_error=True)
        PosOrder._cron_report_retail_pos(session_ids=self.ids, automatic=False, raise_for_error=True)
