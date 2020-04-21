# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import logging
import operator

_logger = logging.getLogger(__name__)


def is_pair(x):
    return not x % 2


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def get_fedicom_product_code(self, supplier_id):
        self.ensure_one()
        code = self.with_context(partner_id=supplier_id).code

        eancode = '847000'+code
        check = str((10 - sum((3, 1)[i % 2] * int(n)
            for i, n in enumerate(reversed(eancode)))) % 10)

        return eancode+check
