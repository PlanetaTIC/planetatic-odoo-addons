# Copyright 2019 PlanetaTIC <info@planetatic.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Partner Account Group",
    "summary": "Use accounts from partner group",
    "version": "12.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Accounting",
    "website": "https://www.planetatic.com/",
    "author": "PlanetaTIC",
    "maintainers": ["PlanetaTIC"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        'views/res_partner_views.xml',
    ],
}
