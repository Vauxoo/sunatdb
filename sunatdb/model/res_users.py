# coding: utf-8
##
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
##
#    Coded by: Edgard Pimentel (pimentelrojas@gmail.com)
#              Luis Torres (luis_t@vauxoo.com)
##
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import hashlib
import logging
from datetime import datetime

from openerp import api, fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Inherit res.users to manage the access tokens
    """
    _name = 'res.users'
    _inherit = ['res.users']

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
                                help='True if this user was authorized '
                                'to do request')

    @api.multi
    def random_token(self):
        """ Generates an ID to identify each one of record created
        return the strgin with record ID
        """
        self.ensure_one()
        # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
        token = hashlib.sha256('%s-%s-%s' % (
            datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
            self.id,
            self.login)).hexdigest()
        if self.sudo().search([('access_token', '=', token)]):
            return self.random_token()
        return token

    @api.one
    def generate_sunat_token(self):
        """Generate tokens to allow users do request to get partners
        information
        """
        self.write({'access_token': self.random_token()})
        self.sudo().write({'authorized': True})
        return True
