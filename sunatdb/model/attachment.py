# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo import fields


class IrsAttachment(models.Model):
    _inherit = 'ir.attachment'

    db_check_update = fields.Boolean("SUNAT Padron check update", default=False, copy=False)
