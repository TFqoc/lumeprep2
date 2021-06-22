# -*- coding: utf-8 -*-

from odoo import models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def record_production(self):
        lots_to_check = self.move_line_ids.filtered(lambda ml: ml.product_id.is_metric_product).mapped('lot_id')
        result = lots_to_check.with_context(production=self.production_id.sudo()).show_reserved_documents()
        if result:
            return result
        return super(MrpWorkorder, self).record_production()
