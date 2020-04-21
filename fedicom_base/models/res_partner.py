# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fedicom_user = fields.Char('FEDICOM User', company_dependent=True, size=64)
    fedicom_password = fields.Char('FEDICOM Password', company_dependent=True,
                                   size=64)
    fedicom_supplier_code = fields.Char(
        'Fedicom Supplier Code', size=30, company_dependent=True)
    fedicom_order_type = fields.Char(
        'Fedicom Order Type', size=6, company_dependent=True)
    fedicom_center = fields.Char(
        'Fedicom Center', size=4, company_dependent=True)
