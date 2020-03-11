# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import zipfile
from collections import OrderedDict
from io import BytesIO

import requests

from odoo import api, models

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
        text = result.decode('UTF-8').replace('|-|', '||')
        text = text.split('|')
        name = (text[1] if len(text) >= 14 else '')
        ruc = (text[0] if len(text) >= 14 else '')
        ubigeo = (text[4] if len(text) >= 14 else '')
        for add in len(text) >= 14 and address or []:
            desc = text[address[add]].replace('-', '').strip() and \
                (add in ('6', '8') and text[address[add] - 1] or add) or ''
            val = text[address[add]].replace('-', '').strip() or ''
            desc = desc.strip()
            new = ('%(desc)s %(val)s' % {'desc': desc, 'val': val}).strip()
            street = '%(street)s %(new)s' % {'street': street, 'new': new}
            street = street.strip().replace('\\', '')
        return True, name, name, street, ruc, ubigeo

    @api.model
    def _download_zip_from_sunat(self, url=False):
        _logger.info('Starting Download of the file')
        if not url:
            url = 'http://www2.sunat.gob.pe/padron_reducido_ruc.zip'
        request = requests.get(url)
        _logger.info('Encoding fileload of the file')
        encoded = base64.b64encode(request.content)
        _logger.info('File encoded')
        attachment = self.env['ir.attachment'].search(
            [('mimetype', '=', 'application/zip'),
             ('type', '=', 'binary'),
             ('name', '=', 'padron_reducido_ruc'),
             ('db_check_update', '=', False)], limit=1)
        if not attachment:
            self.env['ir.attachment'].create({
                'datas': encoded,
                'mimetype': 'application/zip',
                'name': "padron_reducido_ruc.zip",
            })
            return
        attachment.update({'datas': encoded})
        _logger.info('File saved and stored')

    @api.model
    def _register_new_partners(self):
        _logger.info('Reading file')
        attachment = self.env['ir.attachment'].search(
            [('mimetype', '=', 'application/zip'),
             ('type', '=', 'binary'),
             ('name', '=', 'padron_reducido_ruc.zip'),
             ('db_check_update', '=', False)], limit=1)
        if not attachment or not attachment.datas:
            _logger.info('Attachment not found or no zip')
            return
        _logger.info('Decoding file')
        try:
            zip_decoded = zipfile.ZipFile(BytesIO(base64.b64decode(attachment.datas)))
            _logger.info('File decoded')
        except zipfile.BadZipfile:
            _logger.info('The zip you are trying to read is not a zipfile')
        _logger.info('Zipfile created, reading .txt inside')
        lines = zip_decoded.read('padron_reducido_ruc.txt')
        _logger.info('Loading partners')
        for register in lines.splitlines()[1:]:
            reg = tuple(self._get_info_from_file(
                register.decode('latin-1').encode('utf8')))
            self._cr.execute('''INSERT INTO
                                    res_partner
                            (  active,
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
        _logger.info('Disabling this attachment')
        attachment.update({'db_check_update': True})
        _logger.info('Attachment disabled')
        _logger.info('Process Finished')
