# -*- coding: utf-8 -*-
##
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 Vauxoo - http://www.vauxoo.com
#    All Rights Reserved.
#    info@vauxoo.com
##
#    Coded by: Edgard Pimentel (pimentelrojas@gmail.com)
#              Luis Torres (luis_t@vauxoo.com)
#              Mariano Fernandez (mariano@vauxoo.com)
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
import base64
import logging
import zipfile
from collections import OrderedDict
from StringIO import StringIO

import requests

from openerp import api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Inherit res.partner to get your name & address from the xml returned by
    SUNAT
    """
    _inherit = 'res.partner'
    _sql_constraints = [
        ('vat_unique', 'UNIQUE(vat)', 'The vat must que unique'),
    ]

    @api.model
    def _get_info_from_file(self, result):
        name = ''
        street = ''
        ruc = ''
        address = OrderedDict()
        address['6'] = 6
        address['KM.'] = 14
        address['NRO.'] = 9
        address['MZA.'] = 13
        address['LOTE.'] = 11
        address['8'] = 8
        address['DEP.'] = 12
        address['INT.'] = 10
        text = result.replace('|-|', '||')
        text = text.split('|')
        name = len(text) >= 14 and text[1] or ''
        ruc = len(text) >= 14 and text[0] or ''
        ubigeo = len(text) >= 14 and text[4] or ''
        for add in len(text) >= 14 and address or []:
            desc = text[address[add]].replace('-', '').strip() and \
                (add in ('6', '8') and text[address[add] - 1] or add) or ''
            val = text[address[add]].replace('-', '').strip() or ''
            desc = desc.strip()
            new = ('%(desc)s %(val)s' % {'desc': desc, 'val': val}).strip()
            street = '%(street)s %(new)s' % {'street': street, 'new': new}
            street = street.strip().replace('\\', '')
        return True, 'none', name, name, street, ruc, ubigeo

    @api.model
    def _download_zip_from_sunat(self, url=False):
        _logger.info('Starting Download of the file')
        if not url:
            url = 'http://www2.sunat.gob.pe/padron_reducido_ruc.zip'
        request = requests.get(url)
        encoded = base64.b64encode(request.content)
        attachment = self.env['ir.attachment'].search(
            [('mimetype', '=', 'application/zip'),
             ('type', '=', 'binary'),
             ('name', '=', 'padron_reducido_ruc'),
             ('db_check_update', '=', False)], limit=1)
        if not attachment:
            self.env['ir.attachment'].create({
                'datas': encoded,
                'mimetype': 'application/zip',
                'name': "padron_reducido_ruc",
                'datas_fname': "padron_reducido_ruc.zip",
            })
            return
        attachment.update({'datas': encoded})

    @api.model
    def _register_new_partners(self):
        _logger.info('Reading file')
        attachment = self.env['ir.attachment'].search(
            [('mimetype', '=', 'application/zip'),
             ('type', '=', 'binary'),
             ('name', '=', 'padron_reducido_ruc'),
             ('db_check_update', '=', False)], limit=1)
        if not attachment:
            return
        encoded = base64.b64decode(attachment.datas)
        zip_decoded = zipfile.ZipFile(StringIO(encoded))
        lines = zip_decoded.read('padron_reducido_ruc.txt')
        _logger.info('Loading partners')
        for register in lines.splitlines()[1:]:
            reg = tuple(self._get_info_from_file(
                register.decode('latin-1').encode('utf8')))
            self._cr.execute('''INSERT INTO
                                    res_partner
                            (  active,
                                notify_email,
                                display_name,
                                name,
                                street,
                                vat,
                                city)
                            VALUES %s
                            ON CONFLICT
                                (vat)
                            DO UPDATE SET
                                display_name = EXCLUDED.display_name,
                                name = EXCLUDED.name,
                                street = EXCLUDED.street,
                                city = EXCLUDED.city;
                            ''', (reg,))
        _logger.info('Queries executed')
        _logger.info('Process Finished')
