# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys
import logging
import os

from os import path

sys.path.append(path.dirname(os.path.abspath('../../fedicom_base/service/')))
from service import server

_logger = logging.getLogger(__name__)

_logger.info('Initializing Fedicom Order Server')

port = int(sys.argv[1])
odoo_info = {
    'url': sys.argv[2],
    'dbname': sys.argv[3],
    'username': sys.argv[4],
    'password': sys.argv[5],
}

_logger.debug('Odoo\'s URL: %s\nDB name: %s\nOdoo username: %s\nOdoo password: %s' %
              (odoo_info['url'], odoo_info['dbname'], odoo_info['username'],
               odoo_info['password']))

my_server = server.ServerThread('0.0.0.0', port, odoo_info)
my_server.start()
