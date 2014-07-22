from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class sale_order_line_make_invoice(osv.osv_memory):
    _inherit = "sale.order.line.make.invoice"
    #_description = "Sale OrderLine Make_invoice"
    
    def make_invoices(self, cr, uid, ids, context=None):
        """
             To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        if context is None: context = {}
        res = False
        invoices = {}

    #TODO: merge with sale.py/make_invoice
        def make_invoice(order, lines):
            """Este metodo de codigo no es DRY, debe mejorarse el codigo base de odoo
            """
            a = order.partner_id.property_account_receivable.id
            if order.partner_id and order.partner_id.property_payment_term.id:
                pay_term = order.partner_id.property_payment_term.id
            else:
                pay_term = False   
            inv = {
                'name': order.client_order_ref or '',
                'origin': order.name,
                'type': 'out_invoice',
                'reference': "P%dSO%d" % (order.partner_id.id, order.id),
                'account_id': a,
                'partner_id': order.partner_invoice_id.id,
                'invoice_line': [(6, 0, lines)],
                'currency_id' : order.pricelist_id.currency_id.id,
                'comment': order.note,
                'payment_term': pay_term,
                'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                'user_id': order.user_id and order.user_id.id or False,
                'company_id': order.company_id and order.company_id.id or False,
                'date_invoice': fields.date.today(),
            }
            
            #fragmento medio repetido de _prepare_invoice de sale.order
            #al momento el framework no nos permite hacerlo mas DRY
            #se podria redefinir toda la funcion make_invoice a fin de que
            #carge todos los datos de _preapre_invoice
            sale_obj = self.pool.get('sale.order')
            invoice_vals = sale_obj._prepare_invoice(cr, uid, order, lines, context)                        
            inv.update(invoice_vals)
            
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv)
            return inv_id

        sales_order_line_obj = self.pool.get('sale.order.line')
        sales_order_obj = self.pool.get('sale.order')
        wf_service = netsvc.LocalService('workflow')
        for line in sales_order_line_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if (not line.invoiced) and (line.state not in ('draft', 'cancel')):
                if not line.order_id in invoices:
                    invoices[line.order_id] = []
                line_id = sales_order_line_obj.invoice_line_create(cr, uid, [line.id])
                for lid in line_id:
                    invoices[line.order_id].append(lid)
        for order, il in invoices.items():
            res = make_invoice(order, il)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, res))
            flag = True
            data_sale = sales_order_obj.browse(cr, uid, order.id, context=context)
            for line in data_sale.order_line:
                if not line.invoiced:
                    flag = False
                    break
            if flag:
                wf_service.trg_validate(uid, 'sale.order', order.id, 'manual_invoice', cr)
                sales_order_obj.write(cr, uid, [order.id], {'state': 'progress'})

        if not invoices:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n1.The state of this sales order line is either "draft" or "cancel"!\n2.The Sales Order Line is Invoiced!'))
        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, res, context=context)
        return {'type': 'ir.actions.act_window_close'}

sale_order_line_make_invoice()


class sale_advance_payment_inv(osv.osv_memory):
    '''se redefine el wizard ya que el base tiene errores
    '''
    
    _inherit = "sale.advance.payment.inv"
    
    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        sale_obj = self.pool.get('sale.order')
        ir_property_obj = self.pool.get('ir.property')
        fiscal_obj = self.pool.get('account.fiscal.position')
        inv_line_obj = self.pool.get('account.invoice.line')
        wizard = self.browse(cr, uid, ids[0], context)
        sale_ids = context.get('active_ids', [])

        result = []
        for sale in sale_obj.browse(cr, uid, sale_ids, context=context):
            val = inv_line_obj.product_id_change(cr, uid, [], wizard.product_id.id,
                    uom_id=False, partner_id=sale.partner_id.id, fposition_id=sale.fiscal_position.id)
            res = val['value']

            # determine and check income account
            if not wizard.product_id.id :
                prop = ir_property_obj.get(cr, uid,
                            'property_account_income_categ', 'product.category', context=context)
                prop_id = prop and prop.id or False
                account_id = fiscal_obj.map_account(cr, uid, sale.fiscal_position or False, prop_id)
                if not account_id:
                    raise osv.except_osv(_('Configuration Error!'),
                            _('There is no income account defined as global property.'))
                res['account_id'] = account_id
            if not res.get('account_id'):
                raise osv.except_osv(_('Configuration Error!'),
                        _('There is no income account defined for this product: "%s" (id:%d).') % \
                            (wizard.product_id.name, wizard.product_id.id,))

            # determine invoice amount
            if wizard.amount <= 0.00:
                raise osv.except_osv(_('Incorrect Data'),
                    _('The value of Advance Amount must be positive.'))
            if wizard.advance_payment_method == 'percentage':
                inv_amount = sale.amount_total * wizard.amount / 100
                if not res.get('name'):
                    res['name'] = _("Advance of %s %%") % (wizard.amount)
            else:
                inv_amount = wizard.amount
                if not res.get('name'):
                    #TODO: should find a way to call formatLang() from rml_parse
                    symbol = sale.pricelist_id.currency_id.symbol
                    if sale.pricelist_id.currency_id.position == 'after':
                        res['name'] = _("Advance of %s %s") % (inv_amount, symbol)
                    else:
                        res['name'] = _("Advance of %s %s") % (symbol, inv_amount)

            # determine taxes
            if res.get('invoice_line_tax_id'):
                res['invoice_line_tax_id'] = [(6, 0, res.get('invoice_line_tax_id'))]
            else:
                res['invoice_line_tax_id'] = False

            # create the invoice
            inv_line_values = {
                'name': res.get('name'),
                'origin': sale.name,
                'account_id': res['account_id'],
                'price_unit': inv_amount,
                'quantity': wizard.qtty or 1.0,
                'discount': False,
                'uos_id': res.get('uos_id', False),
                'product_id': wizard.product_id.id,
                'invoice_line_tax_id': res.get('invoice_line_tax_id'),
                'account_analytic_id': sale.project_id.id or False,
            }

            #fragmento medio repetido de _prepare_invoice de sale.order
            #al momento el framework no nos permite hacerlo mas DRY
            #se podria redefinir toda la funcion make_invoice a fin de que
            #carge todos los datos de _preapre_invoice
            sale_obj = self.pool.get('sale.order')
            invoice_vals = sale_obj._prepare_invoice(cr, uid, sale, None, context)                        
            
            inv_values = {
                'name': sale.client_order_ref or sale.name,
                'origin': sale.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': sale.partner_id.property_account_receivable.id,
                'partner_id': sale.partner_invoice_id.id,
                'invoice_line': [(0, 0, inv_line_values)],
                'currency_id': sale.pricelist_id.currency_id.id,
                'comment': '',
                'payment_term': sale.payment_term.id,
                'fiscal_position': sale.fiscal_position.id or sale.partner_id.property_account_position.id,
                'invoice_address': invoice_vals['invoice_address'],
                'invoice_phone': invoice_vals['invoice_phone'],
                'internal_number': invoice_vals['internal_number'],
                'document_invoice_type_id': invoice_vals['document_invoice_type_id'],
                'authorizations_id': invoice_vals['authorizations_id'],
                'sri_tax_support_id': invoice_vals['sri_tax_support_id'],
            }
            result.append((sale.id, inv_values))
        return result

sale_advance_payment_inv()