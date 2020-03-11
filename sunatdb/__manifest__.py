# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Consulting Partners by RUC",
    'version': '0.1',
    'author': 'Vauxoo',
    'license': 'OEEL-1',
    "depends": [
        "base_vat",
        "auth_oauth",
    ],
    "demo": [],
    "data": [
        'data/ir_cron.xml',
        'view/res_users_view.xml',
        'view/webclient_templates.xml',
    ],
    "installable": True,
    "auto_install": False
}
