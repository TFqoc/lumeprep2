from odoo import models, fields

class NoteWizard(models.TransientModel):
    _name = 'note.wizard'
    _description = 'A wizard for displaying notes'

    partner_id = fields.Many2one('res.partner', readonly=True)
    note_ids = fields.One2many(related='partner_id.note_ids',inverse_name='source_partner_id',store=True,copy=True)
    message = fields.Char('Message', required=True)

    #@api.multi
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}

    def action_create_note(self):
        #create the note object
        self.env['lume.note'].create({
            'logged_partner_id':self.env['res.users'].browse(self.env.uid).partner_id.id,
            'source_partner_id':self.partner_id.id,
            'message':self.message,
            'completed': False,
        })
        #respawn the wizard
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Notes',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'note.wizard',
            'target': 'new',
            'context': {'default_partner_id': self.partner_id.id},
        }