# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id.account_group_id:
            account_group = self.partner_id.account_group_id
            if self.type in ('out_invoice', 'out_refund'):
                self.account_id = account_group.property_account_receivable_id
            else:
                self.account_id = account_group.property_account_payable_id
        return res
