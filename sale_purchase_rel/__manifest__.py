# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Francisco Fernández <ffernandez@planetatic.com>
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Sales Purchases Relations',
    'summary': 'Adds relations between sales and purchases in MTO procurements',
    'version': '10.0.1.0.0',
    'development_status': 'Production/Stable',
    'category': 'Warehouse',
    'website': 'https://www.planetatic.com',
    'author': 'PlanetaTIC',
    'maintainers': ['PlanetaTIC'],
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'sale_stock',
        'purchase',
    ],
    'data': [
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/stock_view.xml',
    ],
}
