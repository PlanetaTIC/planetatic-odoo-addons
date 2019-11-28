# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    account_group_id = fields.Many2one('res.partner', company_dependent=True, string='Accounting group')

    def _commercial_fields(self):
        return super(Partner, self)._commercial_fields() + \
            ['account_group_id']

    def _find_accounting_partner(self, partner):
        if partner.account_group_id:
            return partner.account_group_id
        return super(Partner, self)._find_accounting_partner(partner)
