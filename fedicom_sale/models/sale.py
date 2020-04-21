# -*- coding: utf-8 -*-
# Copyright 2013 NaN·tic <info@nan-tic.com>
# Copyright 2019 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import traceback
import sys
from weakref import WeakSet

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def convertToInt(value):
    try:
        return int(value)
    except:
        return 0


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    from_fedicom = fields.Boolean('Is Fedicom Sale?')

    @api.multi
    def process_order(self, sales, customer_code, password, order, products):
        try:
            return self.process_order_internal(
                sales, customer_code, password, order, products)
        except Exception as e:
            exc_type, exc_value = sys.exc_info()[:2]
            _logger.warning(
                'SALE FEDICOM: Exception processing fedicom order: %s (%s)\n'
                '\t%s' %
                (exc_type, exc_value, traceback.format_exc()))

        # Ensure we free table lock
        _logger.debug("Process Order Internal Failed: %s" % str(e))

        return {"error": 'Internal Error'}

    # Processes an incoming order request
    # products format: [('product_code', amount), ]
    # returns [('product_code', amount, 'reason'), ]
    @api.multi
    def process_order_internal(
            self, sales, customer_code, password, order, products):

        partner_obj = self.env['res.partner']
        fedicomlog_obj = self.env['fedicom.log']
        product_obj = self.env['product.product']
        sale_line_obj = self.env['sale.order.line']

        _logger.info('SALE FEDICOM: Process Order %s from partner %s' %
                     (order, customer_code))

        partner_ids = partner_obj.search([
            ('fedicom_user', '=', customer_code)])

        if not partner_ids:
            # Log error
            fedicomlog_obj.create({
                'message': _('User %s does not exists') % str(customer_code),
            })
            _logger.info('SALE FEDICOM: Customer code %s not found' %
                         customer_code)
            return {
                'error': _('Incorrect Login'),
            }

        partner_id = partner_ids[0]
        if partner_id.fedicom_password != password:
            # Log error, specifying party
            fedicomlog_obj.create({
                'message': _('Incorrect password'),
                'partner_id': partner_id.id
            })
            _logger.info('SALE FEDICOM: Invalid password for user %s' %
                         customer_code)
            return {
                'error': _('Invalid password'),
            }

        sale = self.create({
            'partner_id': partner_id.id,
            'state': 'draft',
        })
        sale.onchange_partner_id()

        # We'll keep the sum of assigned units per product as there might be
        # a product in more than one line (or the same product with different
        # codes due to synonyms) We'll substract this amount to the available
        # stock to be sure we don't go under zero because the stock is
        # substracted once after processing all lines.
        assigned_products = {}
        missing_stock = []
        product_messages = []
        lines = []

        for prod in products:
            if len(prod) > 1:
                _logger.info('SALE FEDICOM: Process: product code %s, qty %s' %
                             (prod[0], str(prod[1])))
            elif len(prod) == 1:
                _logger.info('SALE FEDICOM: Process: %s' % prod)
            product = None
            product_available = None
            # Search the product code within the products
            product_code = product_obj.get_default_code_from_fedicom_code(
                prod[0])
            search_products = product_obj.search([
                ('default_code', '=', product_code),
            ])

            if search_products:
                product = search_products[0]
                product_available = int(product.immediately_usable_qty) or 0

            ordered = convertToInt(prod[1])
            if not product:
                # If product doesn't exist...
                missing_stock.append((prod[0], ordered, 'NOT_WORKED'))
                assigned = 0
                _logger.info("Product %s Not Worked" % prod[0])
            else:
                # If product exists...
                already_assigned = assigned_products.get(product_code, 0)
                available = max(product_available - already_assigned, 0)
                available = max(min(available, product_available), 0)
                if available >= ordered:
                    assigned = ordered
                else:
                    assigned = available
                    missing_stock.append(
                        (prod[0], ordered - assigned, 'NOT_STOCK'))

                assigned_products[product_code] = already_assigned + assigned
                if product.sale_line_warn == 'block':
                    raise UserError(
                        _('Product [%s] %s: %s' %
                          (product.default_code, product.name,
                           product.sale_line_warn_msg)))
                if product.sale_line_warn == 'warning':
                    product_messages.append(product.sale_line_warn_msg)

            _logger.info("Product %s: [%s/%s Misses(%s)]" %
                         (product_code, assigned, ordered, ordered - assigned))

            if assigned:
                line = sale_line_obj.create({
                    'order_id': sale.id,
                    'product_uom_qty': assigned,
                    'sequence': len(lines) + 1,
                    'product_id': product.id,
                    'product_uom': product.uom_id.id
                })
                lines.append(line)

        _logger.info("Process Lines Finished")

        if len(lines) == 0:
            fedicomlog_obj.create({
                'message': _('No products'),
                'partner_id': partner_id.id,
            })

            _logger.info("Returning Misses")
            return {
                'missingStock': missing_stock,
                'productMessages': product_messages,
            }

        sales = self.create_fedicom_sales(sale, lines)
        for sale in sales:
            _logger.info("Order Created: %s" % sale.name)
        msg_error, partner_err = self._check_fedicom_sales(sales)
        if msg_error:
            fedicomlog_obj.create({
                'message': msg_error,
                'partner_id': partner_err,
            })
            _logger.info("Sale of partner %s not accepted." % partner_err)
            return {
                'error': msg_error,
                'missingStock': missing_stock,
                'productMessages': product_messages,
                }
        sales.process_fedicom_sales()
        for sale in sales:
            _logger.info("Order confirmed %s" % sale.name)

        fedicomlog_obj.create({
            'message': 'Nuevo pedido',
            'sale': sale.id,
            'partner_id': partner_id.id,
        })

        _logger.info("Returning Misses")
        return {
            'missingStock': missing_stock,
            'productMessages': product_messages,
        }

    @api.multi
    def create_fedicom_sales(self, sale, lines):
        sale.lines = lines
        sale.from_fedicom = True

        return sale

    @api.multi
    def process_fedicom_sales(self):
        self.action_confirm()

    @api.multi
    def _check_fedicom_sales(self, sales):
        return False, False
