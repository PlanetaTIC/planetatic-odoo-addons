# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    invoice_group = fields.Boolean('Invoice to group', readonly=True, states={
        'draft': [('readonly', False)], 'sent': [('readonly', False)],
        'sale': [('readonly', False)]})

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        self.invoice_group = self.partner_id.customer_invoice_group
        self.onchange_invoice_group()

    @api.multi
    @api.onchange('invoice_group')
    def onchange_invoice_group(self):
        if self.invoice_group:
            self.partner_invoice_id = self.partner_id.customer_invoice_group_id
        else:
            self.partner_invoice_id = \
                self.partner_id.address_get(['invoice'])['invoice']
        self.onchange_partner_invoice_id()

    @api.multi
    @api.onchange('partner_invoice_id')
    def onchange_partner_invoice_id(self):
        self.update({
            'pricelist_id':
                self.partner_invoice_id.property_product_pricelist,
            'payment_term_id':
                self.partner_invoice_id.property_payment_term_id,
        })
