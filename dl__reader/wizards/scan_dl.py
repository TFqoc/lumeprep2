from odoo import models

class ScanDL(models.TransientModel):
    _name = "scan.dl"

    image = fields.Binary("Image", help="Select image here")
    #<field name="image" widget='image' />
    raw_text = fields.Char("Raw Text")

    def confirm_action(self):
        pass