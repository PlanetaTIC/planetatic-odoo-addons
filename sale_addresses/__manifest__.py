# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Sales Addresses",
    "summary": "Improvements in sales addresses",
    "version": "12.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Sales",
    "website": "https://www.planetatic.com/",
    "author": "PlanetaTIC",
    "maintainers": ["PlanetaTIC"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "sale",
    ],
    "data": [
        'views/res_partner_views.xml',
        'views/sale_views.xml',
    ],
}
