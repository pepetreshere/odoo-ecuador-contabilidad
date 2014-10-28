# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 TRESCLOUD Cia Ltda (trescloud.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp import netsvc
from tools.translate import _
import openerp.addons.decimal_precision as dp

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def _default_session(self, cr, uid, context=None):
        '''
        Busca una sesion abierta de TPV y la asigna
        Reutilizamos los metodos de pos order
        Solo si el tipo de documento es retail
        '''
        if context is None:
            context = {}
        session = False
        if 'retail_type' in context:
            if context['retail_type'] == 'quick':
                pos_order_obj = self.pool.get('pos.order')
                session = pos_order_obj._default_session(cr, uid, context)
        return session

    def _get_type(self, cr, uid, context=None):
        '''Tipo por defecto, puede ser quick o regular, 
        si el context no tiene el valor entonces es regular.
        '''
        if context is None:
            context = {}
        return context.get('retail_type', 'regular')
                  
    _columns = {
        'cash': fields.float('Cash'), #TODO: Para que esta este campo??
        'bank': fields.float('Bank'), #TODO: Para que esta este campo??
        'invoice': fields.char('Invoice Number'), #TODO: Eliminar el numero, solo el wizard lo necesita
        'is_done': fields.boolean('Is Done'),
        'session_id' : fields.many2one('pos.session', 'Session', 
                                        #required=True,
                                        select=1,
                                        domain="[('state', '=', 'opened')]",
                                        #states={'draft' : [('readonly', False)]},
                                        readonly=True),
        'retail_type': fields.selection([
            ('quick','Quick Sale Order'),
            ('regular','Regular Sale Order'),
            ],'Type', readonly=True, select=True, change_default=True, track_visibility='always'),

        'sale_payments_ids': fields.one2many('sale.payment.so', 'so_id', 'Sale Payments'),
        #TODO: Script que al instalar actualice las sale ordes viejas a regulares
    }

    #TODO: evaluar si a nivel general el user_id debe ser el gerente de la cuenta o el que registra la operaicon
    _defaults = {        
        'user_id': lambda self, cr, uid, context: uid, #debe ser el usuario que crea el registro, no el gerente de la cuenta 
        'retail_type': _get_type,
        }
        
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        if 'retail_type' in context:
            if context['retail_type'] =='quick':
                if "user_id" in res['value']:
                    del res['value']['user_id']
        return res

    def action_button_confirm(self, cr, uid, ids, context=None):
        '''
        Validamos condiciones de la orden de venta previo a su confirmacion
        '''
        sale_data = self.browse(cr, uid, ids[0], context=context)
        sale_obj = self.pool.get('sale.order')        
        obj = self.browse(cr, uid, ids)
        
        if context is None:
            context = {}
        if obj[0].retail_type == "quick":
            result = {}
            
            #decidimos si lanzar el formulario de partner
            if self._should_launch_partner_form(cr, uid, ids, context):
                return self._partner_form_to_launch(cr, uid, ids, context)
            
            #reescribimos la tienda y el centro de costos con el actual
            #este es un parche temporal pues no se pudo programar el valor por defect para tienda en sale order
            shop_id = False
            project_id = False
            try:
                user = self.pool.get('res.users').browse(cr, uid, uid, context)
                shop_id = user.printer_id.shop_id.id
                project_id = user.printer_id.shop_id.project_id.id
            except:
                raise osv.except_osv(_('Error!'), _('Debe configurar un punto de impresion en el usuario'))

            #reescribimos la sesion de TPV con la actual
            current_session_id = self._default_session(cr, uid, context)
            sale_data.write({
                             'session_id': current_session_id,
                             'shop_id': shop_id,
                             'project_id': project_id
                             })
            sale_data = self.browse(cr, uid, sale_data.id, context) #actualizmos el objeto para tener el session_id actualizado
            
            if not self._validate_quick_sale_order(cr, uid, ids, context):
                raise osv.except_osv(_('Error!'), _('An error has ocurred when validating the session and user'))
            """copiar if para el else tambien pero agregar super"""
            """ problema con el calculo realizado por al accion por el contex"""
            view_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale_order_for_retail', 'sale_order_for_retail_wizard_form')
            result = {
                'name': _('Sale Order for Retail'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id and view_id[1] or False,
                'res_model': 'wizard.sale.order.for.retail',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
            }
            if sale_data.pricelist_id.requires_aaproval:
                if sale_data.pricelist_approver_id.id:
                    return result
                else:
                    return self.action_confirm(cr, uid, ids, context)
            else:
                return result
        else:
            return super(sale_order,self).action_button_confirm(cr, uid, ids, context)
            #imprimimos el reporte
            #DR TODO: Andres aki se corre el funcionamiento normal del sistema pedido de venta trambien se imprime???
            #self.print_related_invoice(cr, uid, ids, context)


    def _validate_quick_sale_order(self, cr, uid, ids, context=None):
        '''
        Al momento valida:
        1. Que la sesion de la orden de venta este activa y corresponda al usuario
        '''
        for sale in self.browse(cr, uid, ids, context):
            if sale.retail_type == 'quick':
                if not sale.session_id.id:
                    raise osv.except_osv(_('Error!'), _('A quick sale order requires a POS Session!, please start a POS Session then create a new sale order'))
                if sale.session_id.state != 'opened':
                    raise osv.except_osv(_('Error!'), _('The POS Session state should be In Progress, please start a POS Session then create a new sale order'))
                if sale.session_id.user_id.id != uid:
                    raise osv.except_osv(_('Error!'), _('You are not the user of this POS Session, please start a POS Session then create a new sale order'))
        return True      
        
    def _should_launch_partner_form(self, cr, uid, ids, context=None):
        '''
        Valida que la empresa asociada a la orden de venta tenga todos los datos necesarios
        Esta funcion es implementada en otros modulos, es posteriormente redefinida
        #TODO: Implementar ejemplo de funcion
        '''
        try:
            return super(sale_order, self)._should_launch_partner_form(cr, uid, ids, context)
        except:
            return False
        return False
    
    def _partner_form_to_launch(self, cr, uid, ids, context=None):
        '''
        Formulario de partner a lanzar en caso de que la empresa no tuviera los datos completos
        Esta funcion es implementada en otros modulos, es posteriormente redefinida
        #TODO: Implementar ejemplo de funcion
        '''
        try:
            return super(sale_order, self)._partner_form_to_launch(cr, uid, ids, context)
        except:
            return False
        return False
        
    def copy(self, cr, uid, order_id, default=None, context=None):
        if default is None:
            default = {}
        
        #La sesion no debe copiarse, ej. si duplico una venta de hace un mes.
        pos_order_obj = self.pool.get('pos.order')
        session_id = pos_order_obj._default_session(cr, uid, context)
        
        default.update({
            'sale_payments_ids': [],
            'cash': 0,
            'bank': 0,
            'is_done': False,
            'invoice': False,
            'session_id': False
        })
        return super(sale_order, self).copy(cr, uid, order_id, default, context)

    #TODO: Validar el uso de esta funcion
    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []
        partial_data = {}

        for line in order_lines:
            if line.state == 'done':
                continue

            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                else:
                    move_id = False

                proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
                proc_ids.append(proc_id)
                line.write({'procurement_id': proc_id})
                self.ship_recreate(cr, uid, order, line, move_id, proc_id)
                partial_data['move%s' % (move_id)] = {'product_id': line.product_id.id,
                                                      'product_qty': line.product_uom_qty,
                                                      'product_uom': line.product_uom and line.product_uom.id or False, }
        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            picking_obj.draft_validate(cr, uid, [picking_id], context=None)
            picking_obj.do_partial(cr, uid, [picking_id], partial_data, context=None)
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        return True
    #funcion crear el asiento ELIMINAR DR
    def add_payment(self, cr, uid, order_id, data, context=None):
        """Create a new payment for the order"""
        if not context:
            context = {}
        #voucher_obj = self.pool.get('account.voucher')
        property_obj = self.pool.get('ir.property')
        order = self.browse(cr, uid, order_id, context=context)
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', time.strftime('%Y-%m-%d')),
            'name': order.name + ': ' + (data.get('payment_name', '') or ''),
        }

        account_def = property_obj.get(cr, uid, 'property_account_receivable', 'res.partner', context=context)
        args['account_id'] = (order.partner_id and order.partner_id.property_account_receivable \
                             and order.partner_id.property_account_receivable.id) or (account_def and account_def.id) or False
        args['partner_id'] = order.partner_id and order.partner_id.id or None

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (order.partner_id.name, order.partner_id.id,)
            raise osv.except_osv(_('Configuration Error!'), msg)

        context.pop('session_id', False)

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        for statement in order.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break

        if not statement_id:
            raise osv.except_osv(_('Error!'), _('You have to open at least one cashbox.'))

        args.update({
            'statement_id' : statement_id,
            'pos_statement_id' : order_id,
            'journal_id' : journal_id,
            'type' : 'customer',
            'ref' : order.session_id.name,
        })

        voucher_obj.create(cr, uid, args, context=context)

        return statement_id
    
    
    def print_related_invoice(self, cr, uid, ids, context=None):
        '''
        Imprime las facturas aprobadas asociadas a las ordenes de venta seleccionadas
        Solo funciona cuando hay una unica factura emitida por una restriccion
        '''
        sale_data = self.browse(cr, uid, ids[0], context=context)
        invoices = sale_data.invoice_ids
        for invoice in invoices: #solo trabajamos con la primera factura
            invoice_obj = self.pool.get('account.invoice')
            return invoice_obj.invoice_print(cr, uid, [invoice.id], context=None)
        raise osv.except_osv(
                    _('Error!'),
                    _('There is not an associated invoice to print'))

sale_order()


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"
    
    def _amount_total_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
        return res
    def _amount_tax_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total_included']-taxes['total'])
        return res
    
    def _amount_price_unit(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
#             taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, price)
        return res
# DR funcion validas para mostrar en pantalla despues del onchange en el precio unitario    
    def onchange_amounts(self, cr, uid, ids,product_id,price_unit, product_uom_qty,tax_id,discount,partner_id,pricelist_id, context=None):
        context = context or {}
        if price_unit ==0:
            return {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        pri_obj = self.pool.get('product.pricelist')
        
        taxs= tax_obj.browse(cr, uid, tax_id[0][2])
        pricelist_obs= pri_obj.browse(cr, uid, pricelist_id)
        res = {}
        total = {}
        if context is None:
            context = {}
   # for line in self.browse(cr, uid, ids, context=context):
        price = price_unit * (1 - (discount or 0.0) / 100.0)
        taxes = tax_obj.compute_all(cr, uid, taxs, price, product_uom_qty, product_id, partner_id)
        cur = pricelist_obs.currency_id
        res[id] = cur_obj.round(cr, uid, cur, taxes['total_included'])
        total[id] = cur_obj.round(cr, uid, cur, taxes['total'])
    #return res
        value = {
            'price_unit2':price,
            'price_subtotal':total[id],
            'tax_line':res[id]-total[id],
            'price_total_line': res[id]
        }
#         if product_uom_qty:
        return {'value': value}
#         warning = {
#             'title': _('Warning!'),
#             'message' : _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
#         }
#         return {'warning': warning, 'value': value}
    
       
    _columns = {
        #'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account')),
        'price_total_line': fields.function(_amount_total_line, string='Total', digits_compute= dp.get_precision('Account')),    
        'tax_line': fields.function(_amount_tax_line, string='Tax line', digits_compute= dp.get_precision('Account')),    
        'price_unit2': fields.function(_amount_price_unit, string='Price Unit', digits_compute= dp.get_precision('Account')), 

        #'price_total_line': fields.float('Price total', required=True, digits_compute= dp.get_precision('price total')),
        #'tax_line': fields.float('Product Tax', required=True, digits_compute= dp.get_precision('Product Tax')),
    }
    _defaults = {        
        #'price_unit2': lambda obj, cr, uid, context: obj.price_unit
        }
sale_order_line()



















