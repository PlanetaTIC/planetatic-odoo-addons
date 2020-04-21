# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from datetime import datetime


class FedicomLog(models.Model):
    _name = 'fedicom.log'

    message = fields.Char('Message', required=True)
    timestamp = fields.Datetime('Timestamp', default=datetime.now())
    partner_id = fields.Many2one('res.partner', 'Customer')
