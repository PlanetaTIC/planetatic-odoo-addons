# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FedicomLog(models.Model):
    _inherit = 'fedicom.log'

    purchase_id = fields.Many2one('purchase.order', 'Purchase')
