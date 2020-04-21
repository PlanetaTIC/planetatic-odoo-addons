# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from socket import *
import logging
from messages.close_session import *


_logger = logging.getLogger(__name__)


class Socket:

    def __init__(self, sock=None):
        if sock is None:
            self.socket = socket(AF_INET, SOCK_STREAM)
        else:
            self.socket = sock
            self.socket.settimeout(120)

    def connect(self, host='localhost', port=5000):
        self.socket.connect((host, port))

    def disconnect(self):
        self.socket.shutdown(SHUT_RDWR)
        self.socket.close()

    def send(self, msg, exception=False, traceback=None):
        self.socket.sendall(msg)

    def recieve(self):
        try:
            data = ''
            ch = self.socket.recv(1)
            data += ch
            close = str(CloseSession())
            while True:
                # _logger.debug('FEDICOM NAN_SOCKET: Waiting for reply')
                ch = self.socket.recv(1)
                # When len(ch) == 0 it means the other end has
                # closed the socket
                if len(ch) == 0:
                    _logger.info(
                        'FEDICOM NAN_SOCKET: '
                        "the other end has closed connection. "
                        "Information received till now: '%s'" %
                        data)
                    return None
                # _logger.debug("info received on socket")
                data += ch
                # _logger.debug('FEDICOM NAN_SOCKET: '
                #               'Receiving data : %s :=> %s ' % (ch, data))
                if data[len(data)-len(close):] == close:
                    _logger.debug('FEDICOM NAN_SOCKET: data reception done')
                    break

        except Exception as e:
            _logger.error('FEDICOM NAN_SOCKET: '
                          'Error while receiving data, %s ' % e)
            return None

        _logger.debug('FEDICOM NAN_SOCKET: Received data %s' % data)

        return data
