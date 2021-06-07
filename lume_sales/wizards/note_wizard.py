from odoo import models, fields, api

class NoteWizard(models.TransientModel):
    _name = 'note.wizard'
    _description = 'A wizard for displaying notes'

    partner_id = fields.Many2one('res.partner', readonly=True)
    note_ids = fields.Many2many(comodel_name='lume.note')
    message = fields.Char('Message', required=True)

    #@api.multi
    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}

    def _compute_notes(self):
        self.note_ids = self.env['lume.note'].search([('source_partner_id','=',self.partner_id.id)])

    @api.model
    def create(self, vals):
        # partner = self.env['res.partner'].browse(vals.get('partner_id'))
        notes = self.env['lume.note'].search([('source_partner_id','=',vals.get('partner_id'))])
        vals['note_ids'] = []
        for note in notes:
            vals['note_ids'].append((4,note.id,0))
        return super(NoteWizard, self).create(vals)

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