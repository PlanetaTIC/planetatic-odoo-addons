# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import api, models


class Module(models.Model):
    _inherit = 'ir.module.module'

    @api.multi
    def action_view_cloc(self):
        cloc_obj = self.env['module.cloc']
        if self:
            module_ids = self.mapped('id')
        elif self.env.context.get('active_ids'):
            module_ids = self.env.context['active_ids']
        else:
            module_ids = []
        cloc_ids = []
        for module_id in module_ids:
            cloc = cloc_obj.search([('module_id', '=', module_id)], limit=1)
            if cloc:
                cloc = cloc[0]
            else:
                cloc = cloc_obj.create({'module_id': module_id})
            cloc_ids.append(cloc.id)
        action = self.env.ref('module_cloc.action_cloc').read()[0]
        if len(cloc_ids) > 1:
            action['domain'] = [('id', 'in', cloc_ids)]
        elif len(cloc_ids) == 1:
            action['views'] = [(self.env.ref('module_cloc.view_cloc_form').id,
                                'form')]
            action['res_id'] = cloc.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
