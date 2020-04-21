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

    def get_default_code_from_fedicom_code(self, fedicom_product_code):
        if len(fedicom_product_code) == 13:
            code = fedicom_product_code[6:12]
        else:
            code = fedicom_product_code

        return code
