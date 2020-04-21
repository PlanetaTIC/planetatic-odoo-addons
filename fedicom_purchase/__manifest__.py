# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fedicom Purchase",
    "summary": """When confirming a purchase order of a Fedicom supplier,
sents the purchase information through Fedicom protocol
and treats its response""",
    "development_status": "Production/Stable",
    "version": "10.0.1.0.0",
    "category": "Purchase",
    "website": "https://www.planetatic.com",
    "author": "NaN·tic,"
              "PlanetaTIC",
    "maintainers": ["PlanetaTIC"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "fedicom_base",
        "sale",
    ],
    "data": [
        "views/res_partner_view.xml",
        "views/purchase_view.xml",
        "views/fedicomlog_view.xml",
    ],
}
