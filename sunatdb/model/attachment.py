# -*- coding: utf-8 -*-
# Copyright 2017 Vauxoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models
from openerp import fields


class IrsAttachment(models.Model):
    _inherit = 'ir.attachment'

    db_check_update = fields.Boolean("SUNAT Padron check update",
                                     default=False, copy=False)
    db_zip = fields.Binary(string="File to store the SUNAT RUC database")
