# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    customer_invoice_group = fields.Boolean(company_dependent=True, string='Invoice customer to group')
    customer_invoice_group_id = fields.Many2one('res.partner', domain="[('customer', '=', True)]", company_dependent=True, string='Customer invoice group')

    def _commercial_fields(self):
        return super(Partner, self)._commercial_fields() + \
            ['customer_invoice_group', 'customer_invoice_group_id']
