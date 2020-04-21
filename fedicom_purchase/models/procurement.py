# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, registry
from odoo.exceptions import UserError, ValidationError


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    def _make_po_get_domain(self, partner):
        domain = super(ProcurementOrder, self)._make_po_get_domain(partner)
        domain += (('fedicom_sent', '=', False),)
        if self._context.get('fedicom_procurement_group_id', False):
            domain += ((
                'group_id',
                '=',
                self.env.context['fedicom_procurement_group_id']),)
        else:
            domain += (('fedicom_incidence', '=', False),)

        return domain
