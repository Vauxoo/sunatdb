# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import logging
from datetime import datetime

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Inherit res.users to manage the access tokens
    """
    _inherit = 'res.users'

    def __init__(self, pool, cr):
        """ Override of __init__ to add access rights on
        notification_email_send and alias fields. Access rights are disabled by
        default, but allowed on some specific fields defined in
        self.SELF_{READ/WRITE}ABLE_FIELDS.
        """
        init_res = super(ResUsers, self).__init__(pool, cr)
        # duplicate list to avoid modifying the original reference
        self.SELF_WRITEABLE_FIELDS.append('access_token')
        self.SELF_READABLE_FIELDS.extend(['access_token', 'authorized'])
        return init_res

    access_token = fields.Char('Access Token',
                               help='Token to authorize the requests')
    authorized = fields.Boolean('Authorized',
                                help='True if this user was authorized to do request')

    def random_token(self):
        """ Generates an ID to identify each one of record created
        return the string with record ID
        """
        self.ensure_one()
        # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
        code = '%s-%s-%s' % (
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y%m%d%H"),
            self.id, self.login)
        token = hashlib.sha256(code.encode()).hexdigest()
        if self.sudo().search([('access_token', '=', token)]):
            return self.random_token()
        return token

    def generate_sunat_token(self):
        """Generate tokens to allow users do request to get partners
        information
        """
        self.write({'access_token': self.random_token()})
        self.sudo().write({'authorized': True})
        return True
