# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import json
import subprocess

from odoo import api, fields, models
from odoo.modules.module import get_module_path

CLOC_HEADER_FIELDS = [
    'cloc_url',
    'cloc_version',
    'elapsed_seconds',
    'files_per_second',
    'lines_per_second',
    'n_files',
    'n_lines',
]
CLOC_LANG_FIELDS = [
    'blank',
    'code',
    'comment',
    'nFiles',
]


class ModuleCloc(models.Model):
    _name = 'module.cloc'
    _description = 'Lines of code'
    _rec_name = 'module_id'

    module_id = fields.Many2one('ir.module.module', string='Module',
                                required=True, index=True)

    cloc_url = fields.Char(string='cloc URL')
    cloc_version = fields.Char(string='cloc version')
    elapsed_seconds = fields.Float('Elapsed seconds', digits=(16, 2))
    files_per_second = fields.Float('Files per second', digits=(16, 1))
    lines_per_second = fields.Float('Lines per second', digits=(16, 1))
    n_files = fields.Integer('Number of files')
    n_lines = fields.Integer('Number of lines')

    lang_ids = fields.One2many('module.cloc.lang', 'cloc_id',
                               string='Languages', copy=True)

    sum_nFiles = fields.Integer('Number of files')
    sum_blank = fields.Integer('Blank lines')
    sum_comment = fields.Integer('Comment lines')
    sum_code = fields.Integer('Code lines')

    @api.multi
    def action_count_loc(self):
        cloc_lang_obj = self.env['module.cloc.lang']
        if self:
            clocs = self
        elif self.env.context.get('active_ids'):
            clocs = self.browse(self.env.context['active_ids'])
        else:
            clocs = []
        for cloc in clocs:
            # generate report
            module_path = '%s/' % get_module_path(cloc.module_id.name)
            report_json = subprocess.check_output(
                ['cloc', '--json', module_path])
            report_vals = json.loads(report_json)
            # save header
            report_header_vals = report_vals.get('header', {})
            cloc_vals = {f: report_header_vals.get(f)
                         for f in CLOC_HEADER_FIELDS}
            cloc.write(cloc_vals)
            # save langs
            cloc_lang_dict = {cl.lang: cl for cl in cloc.lang_ids}
            for report_lang, report_lang_vals in report_vals.items():
                if report_lang == 'header':
                    continue
                if report_lang == 'SUM':
                    cloc_sum_vals = {'sum_%s' % f: report_lang_vals.get(f)
                                     for f in CLOC_LANG_FIELDS}
                    cloc.write(cloc_sum_vals)
                    continue
                if report_lang in cloc_lang_dict:
                    cloc_lang = cloc_lang_dict[report_lang]
                else:
                    cloc_lang = cloc_lang_obj.create({
                        'cloc_id': cloc.id,
                        'lang': report_lang,
                    })
                cloc_lang_vals = {f: report_lang_vals.get(f)
                                  for f in CLOC_LANG_FIELDS}
                cloc_lang.write(cloc_lang_vals)
            # delete langs
            cloc_langs = set(cloc.lang_ids.mapped('lang'))
            report_langs = set(report_vals.keys())
            for lang in cloc_langs - report_langs:
                cloc_lang_dict[lang].unlink()
        return True


class ModuleClocLang(models.Model):
    _name = 'module.cloc.lang'
    _description = 'Language'
    _rec_name = 'lang'
    _order = 'cloc_id, lang'

    cloc_id = fields.Many2one('module.cloc', string='Report', required=True,
                              ondelete='cascade', index=True, copy=False)

    lang = fields.Char(string='Language', required=True)
    nFiles = fields.Integer('Number of files')
    blank = fields.Integer('Blank lines')
    comment = fields.Integer('Comment lines')
    code = fields.Integer('Code lines')
