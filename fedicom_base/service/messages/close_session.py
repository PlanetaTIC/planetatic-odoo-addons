# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from message import *


class CloseSession(Message):

    def __init__(self, message=None):
        if message:
            self.code = message[0:2]
            self.subcode = message[2:4]
        else:
            self.code = messages['CLOSE_SESSION_CODE']
            self.subcode = messages['CLOSE_SESSION_SUBCODE']

    def check(self):
        if self.code != messages['CLOSE_SESSION_CODE']:
            return False
        if self.subcode != messages['CLOSE_SESSION_SUBCODE']:
            return False
        return True

    def length(self):
        return messages['CLOSE_SESSION_LENGTH_MESSAGE']

    def __str__(self, *args):
        return messages['CLOSE_SESSION_CODE'] + \
            messages['CLOSE_SESSION_SUBCODE'] + \
            messages['END_MESSAGE']
