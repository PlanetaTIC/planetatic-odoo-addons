# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Francisco Fernández <ffernandez@planetatic.com>
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from openerp import models, fields, api


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.one
    def _get_out_in_picking_ids(self):
        out_in_pickings = []
        for move in self.move_lines:
            if move.out_in_picking_ids:
                in_pick_ids = [pick.id for pick in move.out_in_picking_ids]
                out_in_pickings += in_pick_ids
                out_in_pickings = list(set(out_in_pickings))
        self.out_in_picking_ids = self.browse(out_in_pickings)

    @api.one
    def _get_in_out_picking_ids(self):
        in_out_pickings = []
        for move in self.move_lines:
            if move.in_out_picking_id:
                in_out_pickings.append(move.in_out_picking_id.id)
        self.in_out_picking_ids = self.browse(in_out_pickings)

    out_in_picking_ids = fields.One2many(
        'stock.picking',
        compute='_get_out_in_picking_ids',
        string='In pickings associated to this out picking',
    )
    in_out_picking_ids = fields.One2many(
        'stock.picking',
        compute='_get_in_out_picking_ids',
        string='Out pickings associated to this in picking',
    )

    @api.multi
    def action_view_pickings(self, in_pickings):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if len(in_pickings) > 1:
            action['domain'] = [('id', 'in', in_pickings.ids)]
        elif len(in_pickings) == 1:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')
            ]
            action['res_id'] = in_pickings[0].id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_view_out_in_pickings(self):
        in_picking_ids = []
        if self.ids:
            for picking_in in self.out_in_picking_ids:
                in_picking_ids.extend(picking_in.ids)
        action_window_vals = self.action_view_pickings(
            self.browse(in_picking_ids)
        )
        return action_window_vals

    @api.multi
    def action_view_in_out_pickings(self):
        out_picking_ids = []
        if self.ids:
            for picking_out in self.in_out_picking_ids:
                out_picking_ids.extend(picking_out.ids)
        action_window_vals = self.action_view_pickings(
            self.browse(out_picking_ids)
        )
        return action_window_vals


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.one
    def _get_out_in_picking_ids(self):
        in_picking_ids = []
        in_moves = self.search([
                ('move_dest_id', '=', self.id),
                ('picking_type_id.code', '=', 'incoming'),
            ])
        for in_move in in_moves:
            if in_move.picking_id:
                in_picking_ids.append(in_move.picking_id.id)
        self.out_in_picking_ids = self.env['stock.picking'].browse(
            in_picking_ids
        )

    @api.one
    def _get_in_out_picking_id(self):
        if not self.id:
            return
        out_picking_id = []
        in_moves = self.search([
                ('id', '=', self.id),
                ('picking_type_id.code', '=', 'incoming'),
            ])
        for in_move in in_moves:
            out_move = self.search([
                ('move_orig_ids', '=', in_move.id),
                ('picking_type_id.code', '=', 'outgoing'),
            ])
            if out_move.picking_id:
                out_picking_id.append(out_move.picking_id.id)
        self.in_out_picking_id = self.env['stock.picking'].browse(
            out_picking_id
        )

    out_in_picking_ids = fields.One2many(
        'stock.picking',
        compute='_get_out_in_picking_ids',
        string='In pickings associated to this out move',
    )
    in_out_picking_id = fields.Many2one(
        'stock.picking',
        compute='_get_in_out_picking_id',
        string='Out picking associated to this in move',
    )

    @api.multi
    def action_view_out_in_pickings(self):
        in_picking_ids = []
        if self.ids:
            for in_move in self.out_in_picking_ids:
                in_picking_ids.extend(in_move)
        action_window_vals = self.env['stock.picking'].action_view_pickings(
            in_picking_ids
        )
        return action_window_vals

    @api.multi
    def action_view_in_out_picking(self):
        out_picking_id = []
        if self.ids:
            for out_move in self.in_out_picking_id:
                out_picking_id.extend(out_move)
        action_window_vals = self.env['stock.picking'].action_view_pickings(
            out_picking_id
        )
        return action_window_vals
