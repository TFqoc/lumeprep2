from odoo import models, fields, api

class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    onfleet_api_key = fields.Char(string="API Key")

    # Save Transient data to parameter table
    def set_values(self):
        res = super(Settings, self).set_values()
        config = self.env['ir.config_parameter']
        config.set_param('onfleet_lume.onfleet_api_key', self.onfleet_api_key)
        return res

    # Retrieve parameter data from parameter table on load of this transient model
    @api.model
    def get_values(self):
        res = super(Settings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        api_key = ICPSudo.get_param('onfleet_lume.onfleet_api_key')
        res.update({
            'onfleet_api_key': api_key,
        })
        return res