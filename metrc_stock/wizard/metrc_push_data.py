# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class MetrcPushData(models.TransientModel):
    _name = "metrc.push.data"
    _description = "Metrc Push Data"

    metrc_account_id = fields.Many2one('metrc.account')
    warehouse_id = fields.Many2one('stock.warehouse')
    sync_start_date = fields.Date(help='Date from when you want to sync incoming transfers.')

    def launch(self):
        self.ensure_one()
        account = self.metrc_account_id
        license = self.warehouse_id.license_id
        adjust_reason = self.env['metrc.package.adjust.reason'].search([('license_id', '=', license.id), ('name', '=', 'Incorrect Quantity')])
        if not account:
            raise UserError(_("Can not proceed with the execution. No metrc account associated to the user {}". format(self.env.user.name)))
        if not adjust_reason:
            raise UserError(_("Metrc adjustment reason 'Incorrect Quantity' not found for license {}".format(license.license_number)))
        locations = self.env['stock.location'].search([('location_id', 'child_of', self.warehouse_id.view_location_id.id), ('usage', '=', 'internal')])
        lots_to_process = self.env['stock.production.lot'].search([('is_metric_product', '=', True), ('quant_ids.location_id', 'in', locations.ids)])
        lots_to_process = lots_to_process.filtered(lambda l: l.metrc_id == 0)
        if not lots_to_process:
            raise UserError(_("No metrc lots found to push in warehouse {}.".format(self.warehouse_id.name)))
        lot_count_dict = {}
        for lot in lots_to_process:
            metrc_tag = lot._get_metrc_name()
            if metrc_tag not in lot_count_dict.keys():
                lot_count_dict[metrc_tag] = 0
            lot_count_dict[metrc_tag] += 1
        duplicate_lots = lots_to_process.filtered(lambda l: lot_count_dict[l._get_metrc_name()] > 1)
        # checking of the same lot number appears for different products in a single warehouse.
        if duplicate_lots:
            message = "Following duplicate lots were found in warehouse {} during pushing pakages to METRC for license {}. Cannot proceed further.\n".format(self.warehouse_id.display_name, license.license_number)
            for dup_lot in duplicate_lots:
                message += "- Product {}, Label {},Quantity {}.\n".format(dup_lot.product_id.name, dup_lot._get_metrc_name(), dup_lot.product_qty)
            raise UserError(_(message))
        # checking for the packages with 0 quantities
        if any([float_is_zero(lot.product_qty, precision_rounding=lot.product_uom_id.rounding) for lot in lots_to_process]):
            message = "Following lots found with 0.00 quantity in warehouse {} during pushing pakages to METRC for license {}. Cannot proceed further.\n".format(self.warehouse_id.display_name, license.license_number)
            for empty_lot in lots_to_process.filtered(lambda l: float_is_zero(l.product_qty, precision_rounding=l.product_uom_id.rounding)):
                message += "- Product {}, Label {}, Quantity {}.\n".format(empty_lot.product_id.name, empty_lot._get_metrc_name(), empty_lot.product_qty)
            raise UserError(_(message))
        #  Setting the parameters which are going to be used in the cron.
        self.env['ir.config_parameter'].set_param('metrc_push_warehouse_id', self.warehouse_id.id)
        self.env['ir.config_parameter'].set_param('metrc_pull_sync_date', self.sync_start_date)
        # changing the responsible of the cron to confirm that all the transactions are going to be performed by the user who is currently processing this wizard.
        package_push_cron = self.env.ref('metrc.cron_metrc_push_packages_to_metrc')
        # scheduling the cron to push packages
        package_push_cron.write({
            'user_id': self.env.user.id,
            'numbercall': 1,
            'nextcall': fields.Datetime.to_string(datetime.now() + relativedelta(minutes=5)),
            'active': True
        })
