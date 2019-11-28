# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if not self.partner_id:
            return
        # force selection of invoice address if there is more than one
        partner_invoice_count = self.env['res.partner'].search([
            ('id', 'parent_of', self.partner_id.id),
            '|',
            ('parent_id', '=', False),
            ('type', '=', 'invoice'),
        ], count=True)
        if partner_invoice_count > 1:
            self.partner_invoice_id = False
        # force selection of shipping address if there is more than one
        partner_shipping_count = self.env['res.partner'].search([
            ('id', 'child_of', self.partner_id.id),
            '|',
            ('type', 'in', ('delivery', 'other')),
            ('parent_id', '=', False),
        ], count=True)
        if partner_shipping_count > 1:
            self.partner_shipping_id = False
