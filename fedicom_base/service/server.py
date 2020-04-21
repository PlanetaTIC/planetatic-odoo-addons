# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import threading
from clientthread import *

import logging
_logger = logging.getLogger(__name__)


class ServerThread(threading.Thread):

    def __init__(self, interface, port, odoo_info):
        threading.Thread.__init__(self)
        self.port = port
        self.interface = interface
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((self.interface, self.port))
        self.socket.listen(5)
        self.threads = []
        self.odoo_info = odoo_info

    def run(self):
        try:
            self.running = True
            while self.running:
                _logger.info('FEDICOM SERVER: Waiting for connections')
                (clientsocket, address) = self.socket.accept()
                _logger.info('FEDICOM SERVER: New connection %s, %s' %
                             (clientsocket, address))
                ct = ClientThread(clientsocket, self.threads, self.odoo_info)
                _logger.info('FEDICOM SERVER: Thread created')
                self.threads.append(ct)
                ct.start()
                _logger.info('FEDICOM SERVER: Thread initialized')
        except Exception as e:
            e.printstack()
            _logger.critical('FEDICOM SERVER:'
                             'Error processing connection %s' % e)
        self.socket.close()
        return False

    def stop(self):
        self.running = False
        for t in self.threads:
            t.stop()
            try:
                if hasattr(socket, 'SHUT_RDWR'):
                    self.socket.shutdown(SHUT_RDWR)
                else:
                    self.socket.shutdown(2)
                    self.socket.close()
            except:
                return False
