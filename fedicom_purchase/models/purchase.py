# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import sys
import traceback
import logging
from decimal import Decimal
from odoo.addons.fedicom_base.service.nan_socket import Socket
from odoo.addons.fedicom_base.service.messages.init_session import InitSession
from odoo.addons.fedicom_base.service.messages.close_session \
    import CloseSession
from odoo.addons.fedicom_base.service.messages.order import Order
from odoo.addons.fedicom_base.service.messages.order_line import OrderLine
from odoo.addons.fedicom_base.service.messages.finish_order import FinishOrder
from odoo.addons.fedicom_base.service.messages.incidence_header \
    import IncidenceHeader
from odoo.addons.fedicom_base.service.messages.incidence_order_line \
    import IncidenceOrderLine

from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)
_ZERO = Decimal(0)

INCIDENCES_SELECTION = [
    ('00', _('Undefined')),
    ('01', _('Without Stock')),
    ('02', _('No Serve')),
    ('03', _('Not Worked')),
    ('04', _('Unknown')),
    ('05', _('Drug')),
    ('06', _('To Order')),
    ('07', _('To Drop Out')),
    ('08', _('Pass to Warehouse')),
    ('09', _('New Speciality')),
    ('10', _('Temporal Drop Out')),
    ('11', _('Drop Out')),
    ('12', _('To Order Ok')),
    ('13', _('Limit Service')),
    ('14', _('Sanity Removed')),
]


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    fedicom_incidence = fields.Boolean('Fedicom Incidence', copy=False)
    fedicom_sent = fields.Boolean('Sent to Fedicom', readonly=True, copy=False)
    fedicom_response = fields.Text('Fedicom Response', readonly=True,
                                   copy=False)

    @api.multi
    def post_fedicom_purchase_message(
            self, unserved_quantities, on_odoo_error=False):
        fedicomlog_obj = self.env['fedicom.log']
        product_obj = self.env['product.product']

        self.ensure_one()

        unserved_reports = []
        free_messages = []
        if unserved_quantities:
            summary = unserved_quantities.pop(0)
            unserved_reports = summary['unserved']
            free_messages = summary['free_text_messages']
        unserved_purchase_id = self.purchase_unserved_quantites(
            unserved_quantities)
        # Attach all Fedicom errors (if any) as a message:
        fedicom_logs = fedicomlog_obj.search(
            [('purchase_id', '=', self.id)])
        error_msgs = []
        for log in fedicom_logs:
            if log.message:
                error_msgs.append(log.message)
        if error_msgs:
            errormsg = '<br/>\n'.join(error_msgs)
            body = _('Supplier %s returned these errors'
                     ' while processing order %s:\n %s') % (
                         self.partner_id.name, self.name, errormsg)
            self.message_post(
                body=body,
                subject=None, message_type='comment',
                subtype=u'mail.mt_comment', parent_id=False,
                attachments=None, content_subtype='html')

        if unserved_purchase_id:
            free_message = ''
            if free_messages:
                free_message = '\n'.join(free_messages)
                free_message = ' ' + free_message + '\n'
            # list incidence lines:
            incidences = []
            for incidence_code, product_code in unserved_reports:
                products = product_obj.search(
                    [('default_code', '=', product_code)])
                if products:
                    product = products[0]
                    product_name = product.name
                else:
                    product_name = ''
                incidence_str = _('<li>Product [%s] %s: %s</li>') % (
                    product_code, product_name,
                    _(dict(INCIDENCES_SELECTION).get(incidence_code)))
                incidences.append(incidence_str)
            unserved_purchase = self.browse(unserved_purchase_id)
            if on_odoo_error:
                error_sentence = _(
                    'Could not confirm purchase %s,'
                    ' but this order has been sent to supplier %s'
                    ' using Fedicom protocol. When you confirm this order,'
                    ' it will be sent again through Fedicom.') % (
                        self.name, self.partner_id.name)
            else:
                error_sentence = _(
                    'Supplier %s could not serve this purchase using'
                    ' Fedicom protocol. Purchase <a href=#'
                    ' data-oe-model=purchase.order data-oe-id=%d>%s</a>'
                    ' has been created.') % (
                        self.partner_id.name,
                        unserved_purchase.id, unserved_purchase.name)
            error_body = _(
                '%s<br/>\n%s<br/>\n Incidences:<br/>\n<ul>%s</ul>') % (
                    error_sentence, free_message, '\n'.join(incidences))
            self.message_post(
                body=error_body, subject=None, message_type='comment',
                subtype=u'mail.mt_comment', parent_id=False, attachments=None,
                content_subtype='html')
            self._add_fedicom_log_error('\n'.join(incidences))
        else:
            if on_odoo_error:
                error_body = _(
                    'Could not confirm purchase %s,'
                    ' but this order has been sent to supplier %s'
                    ' using Fedicom protocol. When you confirm this order,'
                    ' it will be sent again through Fedicom.') % (
                        self.name, self.partner_id.name)
            else:
                error_body = _(
                    'Supplier %s has processed order %s correctly') % (
                        self.partner_id.name, self.name)
            self.message_post(
                body=error_body, subject=None, message_type='comment',
                subtype=u'mail.mt_comment', parent_id=False, attachments=None,
                content_subtype='html')

    @api.multi
    def button_confirm(self):
        res = False
        for purchase in self:
            if purchase.fedicom_incidence:
                raise UserError(_('Purchase %s is a Fedicom incidence'
                                ' and cannot be confirmed') % purchase.name)
            if self.partner_id.supplier_fedicom:
                if purchase.fedicom_sent and not purchase.fedicom_response:
                    raise UserError(
                        _('Purchase %s has been sent to Fedicom but'
                          ' no response was obtained.'
                          ' If you want to sent this purchase'
                          ' again to Fedicom you must uncheck Fedicom Sent')
                        % purchase.name)
                fedicom_response = False
                if not purchase.fedicom_sent:
                    fedicom_response = purchase.request_fedicom_purchase()
                elif purchase.fedicom_response:
                    fedicom_response = purchase.fedicom_response
                unserved_quantities = purchase.treat_fedicom_response(
                    fedicom_response)
                self.post_fedicom_purchase_message(unserved_quantities)
            res = super(PurchaseOrder, purchase).button_confirm()

        return res

    @api.multi
    def _add_fedicom_log_error(self, errormsg):
        fedicomlog_obj = self.env['fedicom.log']

        self.ensure_one()

        cr = registry(self._cr.dbname).cursor()
        fedicomlog_obj = fedicomlog_obj.with_env(
            fedicomlog_obj.env(cr=cr))
        fedicomlog_obj.create({
            'message': errormsg,
            'partner_id': self.partner_id.id,
            'purchase_id': self.id,
        })

        fedicomlog_obj._cr.commit()
        fedicomlog_obj._cr.close()

    @api.multi
    def request_fedicom_purchase(self):
        fedicomlog_obj = self.env['fedicom.log']

        self.ensure_one()

        self.fedicom_sent = True
        self.env.cr.commit()

        # Connecting to Fedicom server:
        if not self.partner_id.fedicom_user\
                or not self.partner_id.fedicom_password\
                or not self.partner_id.fedicom_supplier_code:
            raise UserError(
                _('This supplier has missing Fedicom credentials data'))

        _logger.info('Process Purchase %s From Supplier %s' % (
            self.name, self.partner_id.name))

        if not self.partner_id.fedicom_host\
                or not self.partner_id.fedicom_port:
            raise UserError(_('Missing Fedicom host or port'))

        sock = Socket()
        sock.socket.settimeout(self.partner_id.fedicom_timeout or 30)
        try:
            sock.connect(
                self.partner_id.fedicom_host, self.partner_id.fedicom_port)
        except IOError:
            exc_type, exc_value = sys.exc_info()[:2]
            _logger.warning("Exception connecting to fedicom server: "
                            "%s (%s)\n  %s" % (exc_type, exc_value,
                                               traceback.format_exc()))
            cr = registry(self._cr.dbname).cursor()
            fedicomlog_obj = fedicomlog_obj.with_env(
                fedicomlog_obj.env(cr=cr))
            fedicomlog_obj.create({
                'message': 'error_connecting',
                'partner_id': self.partner_id.id,
                'purchase_id': self.id,
            })

            fedicomlog_obj._cr.commit()
            fedicomlog_obj._cr.close()
            raise UserError(_('Error Connecting to FEDICOM'))

        # sent order to Fedicom:
        msg = self.send_order()
        sock.send(msg)
        data = sock.recieve()
        sock.disconnect()

        self.fedicom_response = data
        self.env.cr.commit()

        return data

    @api.multi
    def send_order(self):
        self.ensure_one()

        msg = ""
        msg += str(InitSession(self.partner_id.fedicom_user,
                               self.partner_id.fedicom_password, ''))
        msg += str(Order(self.partner_id.fedicom_supplier_code, self.name,
                         order_type=self.partner_id.fedicom_order_type or '',
                         enterprise='',
                         warehouse=self.partner_id.fedicom_center or ''))
        quantity = 0
        supplier_id = self.partner_id.id

        for line in self.order_line:
            code = line.product_id.get_fedicom_product_code(supplier_id)
            if not code:
                raise UserError(_('Product %s has no Code') %
                                line.product_id.default_code)
            msg += str(OrderLine(code, int(line.product_qty)))
            quantity += line.product_qty
        f = FinishOrder()
        f.finishOrder(str(len(self.order_line)), int(quantity), 0)
        msg += str(f)
        msg += str(CloseSession())
        return msg

    def treat_fedicom_response(self, fedicom_response):
        purchase_line_obj = self.env['purchase.order.line']
        # Treat response:
        unserved_quantities = self.process_message(fedicom_response)
        if unserved_quantities:
            summary = unserved_quantities[0]
            if summary['lines_to_delete']:
                if len(summary['lines_to_delete']) ==\
                        len(self.order_line):
                    # No single line could be served, abort:
                    raise UserError(_(
                        "Fedicom supplier %s could not serve any"
                        " of the requested products."
                        ) % (self.partner_id.name))
                lines_to_delete = purchase_line_obj.browse(
                    summary['lines_to_delete'])
                lines_to_delete.unlink()
        return unserved_quantities

    def process_message(self, msg):
        _logger.info('Process Order Incidence')

        if not msg:
            self._add_fedicom_log_error(_('No reply received'))
            raise UserError(_('No reply received'))

        res = False
        msg_list = msg.split('\r\n')
        i = 0

        msg = msg_list[i]
        if msg[0:4] == '9999':
            # Error
            _logger.error("An error has occurred, "
                          "Could not login")
            if len(msg) > 4:
                errormsg = msg[4:]
            else:
                errormsg = _('Unexpected trace')
            self._add_fedicom_log_error(errormsg)
            raise UserError(errormsg)
        init_session = InitSession()
        init_session.set_message(msg_list[i])

        i = i + 1
        next_message = init_session.next_state()
        incidence = {}
        incidence_lines = {}
        free_server_messages = []
        while i < len(msg_list) - 1:
            msg = msg_list[i]
            if not msg[0:4] in next_message:
                _logger.warning("An error has occurred, "
                                "frame sent does not belong to next state")
                if len(msg) > 4:
                    errormsg = msg[4:]
                else:
                    errormsg = _('Unexpected trace')
                self._add_fedicom_log_error(errormsg)
                raise UserError(errormsg)

            for state in next_message:
                if msg.startswith(state):
                    if msg.startswith('0199'):
                        _logger.info('Processing Close Session')
                        next_message = None
                        if incidence_lines:
                            res = self.process_incidence(incidence_lines)
                            res[0]['free_text_messages'] = free_server_messages
                        return res
                    elif msg.startswith('2010'):
                        _logger.info('Processing Incidence Header')
                        incidence = IncidenceHeader()
                        incidence.set_msg(msg)
                        if int(incidence.order_rejected)\
                                or int(incidence.type)\
                                or int(incidence.condition_service)\
                                or int(incidence.charge_cooperative)\
                                or int(incidence.charge_deferment)\
                                or int(incidence.pay_deferment)\
                                or int(incidence.additional_charge)\
                                or int(incidence.enterprise)\
                                or int(incidence.warehouse)\
                                or int(incidence.date_send_order)\
                                or int(incidence.day_send_order)\
                                or int(incidence.error_totals):
                            self._add_fedicom_log_error(
                                _('Error while reading header: %s') %
                                incidence.msg)
                            raise UserError(
                                _('Error while reading header: %s') %
                                incidence.msg)
                        next_message = incidence.next_state()
                    elif msg.startswith('2011'):
                        # Free text message
                        free_server_messages.append(msg[4:])
                        continue
                    elif msg.startswith('2015'):
                        _logger.info('Processing Incidence Order Line')
                        incidence_line = IncidenceOrderLine()
                        incidence_line.set_msg(msg)
                        next_message = incidence_line.next_state()
                        product_code = incidence_line.article_code
                        incidence_lines[product_code] = \
                            (int(incidence_line.amount_not_served),
                                incidence_line.incidence_code)
                    else:
                        self._add_fedicom_log_error(
                            _('Unexpected trace, reading message'))
                        raise UserError(_('Unexpected trace, reading message'))
            i = i + 1
        return res

    def process_incidence(self, incidence_lines):
        """Returns a list:
        First item of the returned list is a dictionary with unserved items and
         error messages
        The rest items of the list are dictionaries containing all data
         to create a new order of the unserved items.
        """
        _logger.debug('%s' % incidence_lines)

        unserved_quantities = []
        reports = []
        lines_to_delete = []
        supplier_id = self.partner_id.id
        # Update purchase quantities
        amount = Decimal('0.0')
        for line in self.order_line:
            code = line.product_id.get_fedicom_product_code(supplier_id)
            code = code.rjust(13, '0')
            if code not in incidence_lines:
                continue
            amount, reason = incidence_lines.get(code, (None, None))
            if reason not in dict(INCIDENCES_SELECTION):
                reason = '00'
            reports.append((reason, line.product_id.default_code))
            if amount > 0:
                # get all data about unserved quantities:
                unserved_qty = line.get_unserved_quantity(amount)
                unserved_quantities.append(unserved_qty)
                new_product_qty = line.product_qty - amount
                if new_product_qty > 0:
                    # Update line quantity:
                    line.product_qty = new_product_qty
                    line.fedicom_reply_state = reason
                else:
                    # delete line, but get it's procurement:
                    unserved_qty['from_deleted_line'] = True
                    lines_to_delete.append(line.id)

        summary = {
            'unserved': reports,
            'free_text_messages': [],
            'lines_to_delete': lines_to_delete,
        }
        unserved_quantities.insert(0, summary)
        return unserved_quantities

    def purchase_unserved_quantites(self, unserved_quantities):
        procurement_obj = self.env['procurement.order']
        purchase_line_obj = self.env['purchase.order.line']

        if not unserved_quantities:
            return False

        # get sale group:
        group_id = self.sale_ids and self.sale_ids[0].procurement_group_id and\
            self.sale_ids[0].procurement_group_id.id
        ctx = self._context.copy()
        if group_id:
            ctx['fedicom_procurement_group_id'] = group_id

        unserved_purchase = self.copy(default={
            'order_line': False,
            'group_id': group_id,
        })
        unserved_purchase_id = unserved_purchase.id

        # first partial lines:
        for unserved_qty in unserved_quantities:
            if unserved_qty['from_deleted_line'] or \
                    not unserved_qty['procurement_ids']:
                # create a new purchase order line:
                purchase_line = purchase_line_obj.with_context(ctx).create({
                    'product_id': unserved_qty['product_id'],
                    'product_qty': unserved_qty['product_qty'],
                    'product_uom': unserved_qty['product_uom_id'],
                    'price_unit': unserved_qty['price_unit'],
                    'order_id': unserved_purchase_id,
                    'name': unserved_qty['purchase_line_name'],
                    'date_planned': unserved_qty['purchase_line_date_planned'],
                    'discount': unserved_qty['discount'],
                    'taxes_id': [(6, False, unserved_qty['taxes_id'])],
                })
                if unserved_qty['procurement_ids']:
                    # this is a make to order purchase and we do not want to
                    # lose procurements<->purchase relationship
                    procurements = procurement_obj.browse(
                        unserved_qty['procurement_ids'])
                    procurements.write({
                        'purchase_id': unserved_purchase_id,
                        'purchase_line_id': purchase_line.id,
                    })
            else:
                cur_procurement = procurement_obj.browse(
                    unserved_qty['procurement_ids'][0])
                cur_procurement.with_context(ctx).copy(
                    default={
                        'state': 'confirmed',
                        'product_qty': unserved_qty['product_qty'],
                        'purchase_id': unserved_purchase_id,
                        'purchase_line_id': False,
                    }
                )

        # mark new purchase order as fedicom incidence:
        unserved_purchase.write({'fedicom_incidence': True})

        return unserved_purchase_id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    fedicom_reply_state = fields.Selection(INCIDENCES_SELECTION,
                                           string='Fedicom Reply State')

    def get_unserved_quantity(self, unserved_qty):
        # get all data about unserved quantities:
        res = {
            'product_id': self.product_id.id,
            'product_qty': unserved_qty,
            'product_uom_id': self.product_uom.id,
            'price_unit': self.price_unit,
            'purchase_line_name': self.name,
            'purchase_line_date_planned': self.date_planned,
            'procurement_ids': [proc.id for proc in self.procurement_ids],
            'from_deleted_line': False,
            'discount': self.discount,
            'taxes_id': [tax.id for tax in self.taxes_id],
        }

        return res
