# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Francisco Fernández <ffernandez@planetatic.com>
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.one
    def _get_sale_ids(self):
        sale_ids = []
        for sale_line in self.order_line:
            for sale_line_purchase in sale_line.sale_ids:
                sale_ids.append(sale_line_purchase.id)
        self.sale_ids = self.env['sale.order'].browse(sale_ids)

    sale_ids = fields.One2many(
        'sale.order',
        compute='_get_sale_ids',
        string='Sales associated to this purchase'
    )

    @api.multi
    def action_view_sales(self):
        sales = self.sale_ids
        action = self.env.ref('sale.action_orders').read()[0]
        if len(sales) > 1:
            action['domain'] = [('id', 'in', sales.ids)]
        elif len(sales) == 1:
            action['views'] = [
                (self.env.ref('sale.view_order_form').id, 'form')
            ]
            action['res_id'] = sales.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.one
    def _get_sale_line_ids(self):
        sale_lines = []
        for procurements in self.procurement_ids:
            for procurement in procurements:
                sale_lines.append(procurement.buy_sale_line_id.id)
        self.sale_line_ids = self.env['sale.order.line'].browse(sale_lines)

    @api.one
    def _get_sale_ids(self):
        sales = []
        for sale_line in self.sale_line_ids:
            for order in sale_line.order_id:
                sales.append(order.id)
        self.sale_ids = self.env['sale.order'].browse(sales)

    sale_line_ids = fields.One2many(
        'sale.order.line',
        compute='_get_sale_line_ids',
        string='Sale lines associated to this purchase line',
    )
    sale_ids = fields.One2many(
        'sale.order',
        compute='_get_sale_ids',
        string='Sales associated to this purchase line',
    )

    @api.multi
    def action_view_sales(self):
        sales = self.sale_ids
        action = self.env.ref('sale.action_orders').read()[0]
        if sales:
            if len(sales.ids) == 1:
                action['views'] = [
                    (self.env.ref('sale.view_order_form').id, 'form')
                ]
                action['res_id'] = sales.ids[0]
            else:
                action['view_mode'] = 'tree,form'
                action['domain'] = [('id', 'in', sales.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
