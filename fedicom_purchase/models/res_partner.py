# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    supplier_fedicom = fields.Boolean('Fedicom Supplier')

    fedicom_host = fields.Char('Fedicom Host', size=128)
    fedicom_port = fields.Integer('Fedicom Port')
    fedicom_timeout = fields.Integer('Fedicom Timeout')
