# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fedicom Sale",
    "summary": "Enables a services to listen request through Fedicom protocol, and creates requested sale orders.",
    "development_status": "Production/Stable",
    "version": "10.0.1.0.0",
    "category": "Sale",
    "website": "https://www.planetatic.com",
    "author": "NaN·tic,"
              "PlanetaTIC",
    "maintainers": ["PlanetaTIC"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_available",
        "fedicom_base",
        "sale"
    ],
    "data": [],
}
