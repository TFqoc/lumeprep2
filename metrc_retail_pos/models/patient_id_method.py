# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PatientIDMethod(models.Model):
    _name = 'patient.id.method'
    _description = 'External Patient ID Method'

    name = fields.Char(string='Method Name')

    _sql_constraints = [
        ('method_name_uniq', 'unique (name)', 'Patient ID method with this name already exists!'),
    ]