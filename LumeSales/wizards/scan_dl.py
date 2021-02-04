from odoo import models, fields

class ScanDL(models.TransientModel):
    _name = "scan_dl"

    image = fields.Binary("Image", help="Select image here")
    #<field name="image" widget='image' />
    raw_text = fields.Char("Raw Text")

    def confirm_action(self):
        pass