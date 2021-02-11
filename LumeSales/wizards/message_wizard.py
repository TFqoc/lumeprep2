from odoo import models, fields

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'
    _description = 'A wizard for displaying text messages'

    message = fields.Text('Message', required=True, readonly=True)

    #@api.multi
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}