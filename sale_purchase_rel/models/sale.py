# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Francisco Fernández <ffernandez@planetatic.com>
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def _get_purchase_ids(self):
        purchase_ids = []
        for sale_line in self.order_line:
            for sale_line_purchase in sale_line.purchase_ids:
                purchase_ids.append(sale_line_purchase.id)
        self.purchase_ids = self.env['purchase.order'].browse(purchase_ids)

    purchase_ids = fields.One2many(
        'purchase.order',
        compute='_get_purchase_ids',
        string='Purchases associated to this sale',
    )

    @api.multi
    def action_view_purchases(self):
        purchases = self.purchase_ids
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif len(purchases) == 1:
            action['views'] = [
                (self.env.ref('purchase.purchase_order_form').id, 'form')
            ]
            action['res_id'] = purchases.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    def _get_mto_procurement_ids(self):
        self.mto_procurement_ids = self.env['procurement.order'].search([
                ('sale_line_id', '=', self.id),
                ('rule_id.action', '=', 'move'),
                ('rule_id.procure_method', '=', 'make_to_order')
            ])

    @api.one
    def _get_purchase_line_ids(self):
        purchase_line = []
        for procurements in self.mto_procurement_ids:
            for procurement in procurements:
                purchase_line = procurement.mto_purchase_line_ids
        self.purchase_line_ids = purchase_line

    @api.one
    def _get_purchase_ids(self):
        purchases = []
        for purchase_line in self.purchase_line_ids:
            for order in purchase_line.order_id:
                purchases.append(order.id)
        self.purchase_ids = self.env['purchase.order'].browse(purchases)

    mto_procurement_ids = fields.One2many(
        'procurement.order',
        compute='_get_mto_procurement_ids',
        string='MTO procurements associated to this sale line',
    )
    purchase_line_ids = fields.One2many(
        'purchase.order.line',
        compute='_get_purchase_line_ids',
        string='Purchase lines associated to this sale line',
    )
    purchase_ids = fields.One2many(
        'purchase.order',
        compute='_get_purchase_ids',
        string='Purchases associated to this sale',
    )

    @api.multi
    def action_view_purchase(self):
        purchases = self.purchase_ids
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        if purchases:
            if len(purchases.ids) == 1:
                action['views'] = [
                    (self.env.ref('purchase.purchase_order_form').id, 'form')
                ]
                action['res_id'] = purchases.ids[0]
            else:
                action['view_mode'] = 'tree,form'
                action['domain'] = [('id', 'in', purchases.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
