# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

{
    'name': 'Count Module Lines of Code',
    'version': '10.0.1.0.0',
    'author': 'PlanetaTIC',
    'website': 'https://www.planetatic.com',
    'license': 'LGPL-3',
    'category': 'Extra Tools',
    'depends': [],
    'data': [
        'views/module_cloc_views.xml',
        'views/module_views.xml',
    ],
    'external_dependencies': {
        'bin': [
            'cloc',
        ],
    },
}
