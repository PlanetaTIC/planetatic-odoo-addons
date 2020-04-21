# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from message import *


class FreeText(Message):

    def __init__(self, msg):

        self.code = messages['FREE_TEXT_CODE']
        self.subcode = messages['FREE_TEXT_SUBCODE']
        self.msg = msg

    def msg(self):
        return self.msg

    def setMsg(self, msg):
        self.msg = msg

    def __str__(self):
        return messages['FREE_TEXT_CODE'] +\
            messages['FREE_TEXT_SUBCODE'] +\
            self.msg.ljust(50) +\
            messages['END_MESSAGE']
