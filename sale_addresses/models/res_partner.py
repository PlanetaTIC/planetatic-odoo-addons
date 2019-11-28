# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.depends('commercial_partner_id.ref')
    def _compute_display_name(self):
        super(Partner, self)._compute_display_name()

    def _get_name(self):
        """ Utility method to allow name_get to be overrided without re-browse the partner """
        partner = self
        name = partner.name or ''

        if partner.company_name or partner.parent_id:
            # always show type
            if partner.type in ['invoice', 'delivery', 'other']:
                type = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if name:
                    name = "%s: %s" % (type, name)
                else:
                    name = type
            if not partner.is_company:
                name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
        # show ref
        if partner.commercial_partner_id.ref:
            name = '[%s] %s' % (partner.commercial_partner_id.ref, name)
        if self._context.get('show_address_only'):
            name = partner._display_address(without_company=True)
        if self._context.get('show_address'):
            name = name + "\n" + partner._display_address(without_company=True)
        name = name.replace('\n\n', '\n')
        name = name.replace('\n\n', '\n')
        if self._context.get('address_inline'):
            name = name.replace('\n', ', ')
        if self._context.get('show_email') and partner.email:
            name = "%s <%s>" % (name, partner.email)
        if self._context.get('html_format'):
            name = name.replace('\n', '<br/>')
        if self._context.get('show_vat') and partner.vat:
            name = "%s ‒ %s" % (name, partner.vat)
        return name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        return super(Partner, self.with_context(
            address_inline=True)).name_search(name, args, operator, limit)
