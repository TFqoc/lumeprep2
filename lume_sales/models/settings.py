from odoo import models, fields, api

class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    batch_threshold = fields.Integer(string="Batch Threshold")

    # Save Transient data to parameter table
    def set_values(self):
        res = super(Settings, self).set_values()
        config = self.env['ir.config_parameter']
        config.set_param('lume.batch_threshold', self.batch_threshold)
        return res

    # Retrieve parameter data from parameter table on load of this transient model
    @api.model
    def get_values(self):
        res = super(Settings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        batch_setting = ICPSudo.get_param('lume.batch_threshold')
        res.update({
            'batch_threshold': batch_setting,
        })
        return res