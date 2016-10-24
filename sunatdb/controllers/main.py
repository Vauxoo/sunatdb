# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from openerp import http, _
from openerp.http import request


class SunatdbController(http.Controller):

    @http.route('/rfc', type='http', auth="public", methods=['GET'],
                website=True)
    def validate_email(self, token, user, rfc, **kwargs):

        if request.env['res.users'].sudo().\
                search([('login', '=', user),
                        ('access_token', '=', token),
                        ('authorized', '=', True)]):
            partner_data = request.env['res.partner'].sudo().\
                search_read(domain=[('vat', '=', rfc)],
                            fields=['name', 'street', 'vat', 'city'],
                            limit=1)
            partner_data = partner_data and partner_data[0] or {}
            partner_data.pop('id', 'No')

            partner_data = partner_data or \
                {'error_message': _('Partner with vat %s not found' % rfc)}
        else:
            partner_data = {'error_message': _('The token is not valid')}

        return json.dumps(partner_data)
