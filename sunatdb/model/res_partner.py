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
from openerp import models, api
import requests
import zipfile
import StringIO
from collections import OrderedDict


def resolve_unicode(string, i=0):

    if not isinstance(string, (str, unicode)) or not string:
        return string or ''
    nstr = ''
    if i == 0:
        try:
            nstr = string.encode('utf8', 'ignore')
            return nstr.strip()
        except BaseException:
            i += 1
            return resolve_unicode(string, i)
    elif i == 1:
        try:
            nstr = string.decode('latin1').encode('utf8', 'ignore')
            return nstr.strip()
        except BaseException:
            i += 1
            return resolve_unicode(string, i)
    elif i == 2:
        try:
            nstr = string.encode('latin1', 'ignore')
            return nstr.strip()
        except BaseException:
            i += 1
            return resolve_unicode(string, i)
    else:
        raise
    return nstr.strip()


class ResPartner(models.Model):
    """Inherit res.partner to get your name & address from the xml returned by
    SUNAT
    """
    _inherit = 'res.partner'

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
        for add in address:
            desc = text[address[add]].replace('-', '').strip() and \
                (add in ('6', '8') and text[address[add] - 1] or add) or ''
            val = text[address[add]].replace('-', '').strip() or ''
            desc = desc.strip()
            new = ('%(desc)s %(val)s' % {'desc': desc, 'val': val}).strip()
            street = '%(street)s %(new)s' % {'street': street, 'new': new}
            street = street.strip()
        return name, street, ruc

    @api.model
    def _download_ruc_from_sunat(self):
        r = requests.\
            get('http://www2.sunat.gob.pe/padron_reducido_ruc.zip',
                stream=True)
        zfobj = zipfile.ZipFile(StringIO.StringIO(r.content))
        lines = zfobj.read('padron_reducido_ruc.txt')
        for line in lines.split('\n')[1:]:
            line = resolve_unicode(line)
            name, street, ruc = self._get_info_from_file(line)
            self._cr.execute('''SELECT
                                    id
                                FROM
                                    res_partner
                                WHERE
                                    vat = %s
                                LIMIT 1''', (ruc,))
            if not self._cr.fetchall():
                self._cr.execute('''INSERT INTO res_partner
                                 (notify_email, name, display_name, vat)
                                 VALUES (%s, %s, %s, %s)''',
                                 ('none', name, name, ruc))
