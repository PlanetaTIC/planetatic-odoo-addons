# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Francisco Fernández <ffernandez@planetatic.com>
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields, api


class procurement_order(models.Model):
    _inherit = 'procurement.order'

    @api.one
    def _get_mto_buy_procurement_ids(self):
        mto_buy_procurements = []
        mto_procurements = self.search([
                ('id', 'in', self.ids),
                ('rule_id.action', '=', 'move'),
                ('rule_id.procure_method', '=', 'make_to_order'),
            ])
        if mto_procurements:
            for mto_procurement_move in mto_procurements.move_ids:
                buy_procurements = self.search([
                    ('move_dest_id', 'in', [mto_procurement_move.id]),
                    ('rule_id.action', '=', 'buy'),
                ])
                for buy_procurement in buy_procurements:
                    mto_buy_procurements.append(buy_procurement.id)
        self.mto_buy_procurement_ids = self.browse(mto_buy_procurements)

    @api.one
    def _get_mto_purchase_line_ids(self):
        mto_purchase_lines = []
        for buy_procurement in self.mto_buy_procurement_ids:
            mto_purchase_lines.append(buy_procurement.purchase_line_id.id)
        self.mto_purchase_line_ids = self.env['purchase.order.line'].browse(
            mto_purchase_lines
        )

    @api.one
    def _get_buy_mto_procurement_id(self):
        buy_mto_procurement_id = []
        buy_procurements = self.search([
            ('id', 'in', self.ids),
            ('rule_id.action', '=', 'buy'),
        ])
        for buy_procurement_move_dest in buy_procurements.move_dest_id:
            mto_procurements = self.search([
                ('id', '=', buy_procurement_move_dest.procurement_id.id),
                ('rule_id.action', '=', 'move'),
                ('rule_id.procure_method', '=', 'make_to_order'),
            ])
            buy_mto_procurement_id.append(mto_procurements.id)
        self.buy_mto_procurement_id = self.browse(buy_mto_procurement_id)

    @api.one
    def _get_buy_sale_line_id(self):
        self.buy_sale_line_id = []
        if self.buy_mto_procurement_id:
            self.buy_sale_line_id = self.buy_mto_procurement_id.sale_line_id

    mto_buy_procurement_ids = fields.One2many(
        'procurement.order',
        compute='_get_mto_buy_procurement_ids',
        string='Buy procurements associated to this MTO procurement',
    )
    mto_purchase_line_ids = fields.One2many(
        'purchase.order.line',
        compute='_get_mto_purchase_line_ids',
        string='Purchase lines associated to this MTO procurement',
    )
    buy_mto_procurement_id = fields.Many2one(
        'procurement.order',
        compute='_get_buy_mto_procurement_id',
        string='MTO procurement associated to this buy procurement',
    )
    buy_sale_line_id = fields.Many2one(
        'sale.order.line',
        compute='_get_buy_sale_line_id',
        string='Sale line associated to this buy procurement',
    )
