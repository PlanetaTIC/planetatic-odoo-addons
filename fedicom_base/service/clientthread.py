# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import threading
from _socket import *
import logging
import xmlrpclib
import sys

from .nan_socket import *
from .messages.init_session import InitSession
from .messages.close_session import CloseSession
from .messages.finish_order import FinishOrder
from .messages.incidence_header import IncidenceHeader
from .messages.incidence_order_line import IncidenceOrderLine
from .messages.free_text import FreeText
from .messages.order_line import OrderLine
from .messages.order import Order
from .messages.reject_transmission import RejectTransmission


_logger = logging.getLogger(__name__)


class ClientThread(threading.Thread):

    def __init__(self, sock, threads, odoo_info):
        threading.Thread.__init__(self)
        self.socket = sock
        self.threads = threads
        self.user = None
        self.password = None
        self.date = None
        self.ts = None
        self.odoo_info = odoo_info

        self.article = {}

    def run(self):
        self.running = True
        try:
            self.ts = Socket(self.socket)
        except Exception as e:
            _logger.critical('FEDICOM CLIENTTHREAD: '
                             'Error opening socket, %s' % (e))
            self.socket.close()
            self.threads.remove(self)
            return False

        while self.running:
            try:
                _logger.debug('FEDICOM CLIENTTHREAD: Waiting customer data')
                msg = self.ts.recieve()
                self.running = False
                _logger.debug('Received: %s', msg)
                break
            except Exception as e:
                _logger.critical('FEDICOM CLIENTTHREAD: '
                                 'Error receiving data, %s' % (e))
                self.socket.close()
                self.threads.remove(self)
                return False
        # Processing message:
        # None msg means: Reception data error
        # or no response received in timeout.
        if msg is None:
            _logger.critical('FEDICOM CLIENTTHREAD: '
                             'No data received. Closing socket.')
            self.socket.close()
            self.threads.remove(self)
            return False

        self.process_message(msg)
        self.ts.disconnect()
        self.socket.close()
        self.threads.remove(self)
        return True

    def stop(self):
        self.running = False

    def process_message(self, msg):

        msg_list = msg.split('\r\n')
        i = 0

        _logger.debug('FEDICOM CLIENTTHREAD: Processing '
                      'Init Session Message, %s' % (msg_list[i]))
        init_session = InitSession()
        init_session.set_message(msg_list[i])

        customer_code = self.user = init_session.user_code
        password = self.password = init_session.password
        self.date = init_session.date

        i = i + 1
        next_message = init_session.next_state()
        order = {}
        orderlines = {}
        while i < len(msg_list) - 1:
            _logger.debug('FEDICOM CLIENTTHREAD: Processing '
                          ' Message, %s' % (msg_list[i]))
            msg = msg_list[i]
            if not msg[0:4] in next_message:
                _logger.critical('FEDICOM CLIENTTHREAD: '
                                 'Unknown state,'
                                 ' state %s of possible states: %s' %
                                 (msg[0:4], str(next_message)))
                reject_transmission = RejectTransmission(
                    "Error: sent trace does not belong to nexte state")
                self.ts.send(str(reject_transmission))
                break

            for state in next_message:
                if msg.startswith(state):
                    if msg.startswith('0199'):  # Close Session
                        _logger.debug('FEDICOM CLIENTTHREAD: '
                                      'Closing Session')
                        next_message = None
                        self.process_order(customer_code, password, order)
                        return
                    elif msg.startswith('1010'):  # Order Header
                        orderlines = {}
                        _logger.debug('FEDICOM CLIENTTHREAD: '
                                      'Processing order header')
                        o = Order()
                        o.set_msg(msg)
                        next_message = o.next_state()
                    elif msg.startswith('1020'):
                        _logger.debug('FEDICOM CLIENTTHREAD: '
                                      'Processing Order Line')
                        order_line = OrderLine()
                        order_line.set_msg(msg)
                        next_message = order_line.next_state()
                        orderlines[order_line.article_code] = \
                            int(order_line.amount)
                        self.article[order_line.article_code] = \
                            order_line.article_code

                    elif msg.startswith('1050'):
                        _logger.debug('FEDICOM CLIENTTHREAD: '
                                      'Processing order ending')
                        finish_order = FinishOrder()
                        finish_order.set_msg(msg)
                        next_message = finish_order.next_state()
                        order[o.order_number] = orderlines
                    else:
                        _logger.debug('FEDICOM CLIENTTHREAD: '
                                      'trace no processed.')
                        reject_transmission = RejectTransmission(
                            'Error: Unknown received trace')
                        self.ts.send(str(reject_transmission))
                        return

            i = i + 1
        return

    def to_send_order_lines(self, orderlines):
        lines = []
        for k, v in orderlines.items():
            lines.append((k, v))
        return lines

    def process_order(self, user, password, orders):
        _logger.info('FEDICOM CLIENTTHREAD: Start')

        send = {}

        # Using Odoo's API
        common = xmlrpclib.ServerProxy(
            '{}/xmlrpc/2/common'.format(self.odoo_info['url']))
        version = common.version()
        _logger.debug('FEDICOM CLIENTTHREAD: Version %s' % version)
        sys.stdout.flush()
        uid = common.authenticate(
            self.odoo_info['dbname'], self.odoo_info['username'],
            self.odoo_info['password'], {})
        models = xmlrpclib.ServerProxy(
            '{}/xmlrpc/2/object'.format(self.odoo_info['url']))

        for order in orders:
            orders_to_send = self.to_send_order_lines(orders[order])
            result = models.execute_kw(
                self.odoo_info['dbname'], uid, self.odoo_info['password'],
                'sale.order', 'process_order', [
                    [], [], user.strip(), password.strip(), order, orders_to_send],
                {}
            )
            _logger.info('FEDICOM CLIENTTHREAD: '
                         'Order proceessed, generating reply... %s' % result)
            misses = []
            messages = []
            current_order = orders[order]
            reject_transmission = None
            if result.get('error', False):
                _logger.info('FEDICOM CLIENTTHREAD: %s' % result['error'])
                reject_transmission = RejectTransmission(result['error'])
            else:
                for miss in result['missingStock']:
                    (article, not_served, reason) = miss
                    amount = current_order[article]
                    _logger.info(
                        'FEDICOM CLIENTTHREAD: '
                        "Order %s, Product %s, Requested:%s, Pending %s, "
                        "Reason:%s " % (str(order), str(article),
                                        str(int(amount)), str(int(not_served)),
                                        str(reason)))
                    iline = IncidenceOrderLine(
                        self.article[article], int(amount), int(not_served),
                        reason)
                    misses.append(iline)
                for msg in result['productMessages']:
                    imsg = FreeText(msg)
                    messages.append(imsg)

            send[order] = {}
            send[order]['order'] = orders[order]
            send[order]['misses'] = misses
            send[order]['messages'] = messages
            if reject_transmission is not None:
                send[order]['error'] = reject_transmission

        self.send_data(send)

    def send_data(self, send_data):
        result = str(InitSession(self.user, self.password, self.date))
        for k, order in send_data.items():
            if order.get('error', False):
                self.ts.send(str(order['error']) + str(CloseSession("")))
                return
            result += str(IncidenceHeader(self.user, k))
            order['order']
            for msg in order['messages']:
                result += str(msg)
            for miss in order['misses']:
                result += str(miss)
        result += str(CloseSession(""))
        _logger.info('FEDICOM CLIENTTHREAD: '
                     "Reply: %s" % result.replace("\r\n", "<lf><cr>\r\n"))
        self.ts.send(result)
