# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: TRESCLOUD CIA. LTDA.
# Copyright (C) 2013  trescloud.com
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from osv import fields,osv
import decimal_precision as dp
import re
import time
from tools.translate import _
import netsvc
from mx import DateTime
import datetime

class account_invoice(osv.osv):

    _inherit = "account.invoice"

    _columns = {
                #TRESCLOUD - Talvez deberia usarse solo retention_ids en lugar de retetion_ids y retention_line_ids. 
                'retention_ids':fields.one2many('account.retention', 'invoice_id', 'Retention', states={'paid':[('readonly',True)]}),      
               # 'retention_line_ids':fields.one2many('account.retention.line', 'invoice_id', 'Retention Lines', states={'paid':[('readonly',True)]}),      
               }

#    TRESCLOUD - En este sprint no necesitamos esta funcionalidad, solo lo basico
    def copy(self, cr, uid, id, default={}, context=None):
        if context is None:
            context = {}
        default.update({
            'retention_ids':[],
            'retention_line_ids':[],
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
#    TRESCLOUD - En este sprint no necesitamos esta funcionalidad, solo lo basico
    def action_cancel(self, cr, uid, ids, *args):
     #   ret_line_obj = self.pool.get('account.retention.line')
        context={}
        wf_service = netsvc.LocalService("workflow")
        invoices = self.pool.get('account.invoice')
        invoice_obj=invoices.browse(cr, uid, ids, context)[0]
        retention=self.pool.get('account.retention').search(cr,uid,[('invoice_id','=',invoice_obj.id)])
        retention_obj=self.pool.get('account.retention').browse(cr,uid,retention)
        for lines in retention_obj:
            if lines.state == 'approved':
                    wf_service.trg_validate(uid, 'account.retention', lines.id, 'canceled_signal', cr)
        return super(account_invoice, self).action_cancel(cr, uid, ids, context)

account_invoice()

class account_withhold_line(osv.osv):
    _name = "account.withhold.line"

    _columns = {
            'withhold_id': fields.many2one('account.retention', 'Withhold'),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
            'description': fields.selection([('iva', 'IVA'), ('renta', 'RENTA'), ], 'Impuesto'),
            'tax_base': fields.float('Tax Base', digits_compute=dp.get_precision('Account')),
            'retention_percentage': fields.float('Percentaje Value', digits_compute=dp.get_precision('Account')),
            'tax_amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
           # 'retention_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value',
            #                             store={'account.retention.line': (lambda self, cr, uid, ids, c={}: ids, ['tax_id',], 1)},),
            #'retention_percentage': fields.function(_percentaje_retained, method=True, type='float', string='Percentaje Value'),
            'tax_id':fields.many2one('account.tax.code', 'Tax Code'),
            'tax_ac_id':fields.many2one('account.tax.code', 'Tax Code'),
            }
    
account_withhold_line()

class account_withhold(osv.osv):
        
    _name = 'account.retention'
    _rec_name='number'
        #Funcion para calcular el valor total a retener
    def _total(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for ret in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = ret.invoice_id.currency_id
            for line in ret.retention_line_ids:
                #TRESCLOUD - solo debería haber un campo line.retained_value (borrar line.retained_value_manual)
                if ret.transaction_type == 'purchase':
                    val += line.retained_value
                else:
                    val += line.retained_value_manual
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val)
        return res
    
    def _get_retention(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.retention.line').browse(cr, uid, ids, context=context):
            result[line.retention_id.id] = True
        return result.keys()
    
     #TRESCLOUD - Definir funcion total_vat_withhold en su lugar o como alias
    #retorna el valor total de la funcion
    def _total_iva(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for ret in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = ret.invoice_id.currency_id
            for line in ret.retention_line_ids:
                if line.description == 'iva':
                    #TRESCLOUD - solo debería haber un campo line.retained_value (borrar line.retained_value_manual)
                    if ret.transaction_type == 'purchase':
                        val += line.retained_value
                    else:
                        val += line.retained_value_manual
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val)
        return res

    #TRESCLOUD - Definir funcion total_utilities_withhold en su lugar o como alias
    # Valor total a retener por impuesto a la renta
    def _total_renta(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for ret in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = ret.invoice_id.currency_id
            for line in ret.retention_line_ids:
                if line.description == 'renta':
                    #TRESCLOUD - solo debería haber un campo line.retained_value (borrar line.retained_value_manual)
                    if ret.transaction_type == 'purchase':
                        val += line.retained_value
                    else:
                        val += line.retained_value_manual
            if cur:
                res[ret.id] = cur_obj.round(cr, uid, cur, val)
        return res
    
    def _transaction_type(self, cr, uid, context = None):
        if context is None:
            context = {}
        return context.get('transaction_type', False)
                
    
    _columns = {
        'number': fields.char('Number', size=17, required=False),
        #TRESCLOUD - Deberia usarse un solo campo en lugar de number_purchase y number_sale que se llame "documento origen", asi funciona en la mayoria de documentos
        'number_purchase': fields.char('Retention Number', size=17, required=False, readonly=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
        'number_sale': fields.char('Retention Number', size=17, required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
        'creation_date': fields.date('Creation Date',states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
#        #TRESCLOUD - Authorizations should belong to another module
#        'authorization_purchase_id':fields.many2one('sri.authorization', 'Authorization', required=False, readonly=True),
#        'authorization_sale':fields.char('Authorization', size=10, required=False, readonly=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}, help='This Number is necesary for SRI reports'),
#        'authorization_sale_id':fields.many2one('sri.authorization.supplier', 'Authorization', ),

        #TRESCLOUD - este es usado para el ATS??
        'transaction_type':fields.selection([
            ('purchase','Purchases'),
            ('sale','Sales'),
            ],  'Transaction type', required=True, readonly=True),
#        'retention_line_ids': fields.one2many('account.voucher', 'retention_id', 'Retention Lines'),

        #TRESCLOUD - Removimos el "ondelete='cascade" del invoice_id, puede llevar a borrados inintencionales!
        'invoice_id': fields.many2one('account.invoice', 'Number of document', required=False, states={'approved':[('readonly',True)], 'canceled':[('readonly',True)]}),
        'partner_id': fields.related('invoice_id','partner_id', type='many2one', relation='res.partner', string='Partner', store=True),

        #TRESCLOUD - Deberia guardarse el nombre del partner, su RUC, direccion, etc (ejemplo el año que viene el cliente cambia de direccion,
        # entonces el documento tributario del año 2012 no deberia verse afectado)  
        'company_id': fields.related('invoice_id','company_id', type='many2one', relation='res.company', string='Company', store=True),
        'state':fields.selection([
            ('draft','Draft'),
            ('approved','Approved'),
            ('canceled','Canceled'),
            ],  'State', required=True, readonly=True),
#        'total': fields.function(_total, method=True, type='float', string='Total Retenido', store = {
#                                 'account.retention': (lambda self, cr, uid, ids, c={}: ids, ['retention_line_ids'], 11),
#                                 'account.retention.line': (_get_retention, ['tax_base', 'retention_percentage', 'retained_value',], 11),
#                                 }), 
#        'total_iva': fields.function(_total_iva, method=True, type='float', string='Total IVA', store = {
#                                 'account.retention': (lambda self, cr, uid, ids, c={}: ids, ['retention_line_ids'], 11),
#                                 'account.retention.line': (_get_retention, ['tax_base', 'retention_percentage', 'retained_value',], 11),
#                                 }), 
#        'total_renta': fields.function(_total_renta, method=True, type='float', string='Total Renta', store = {
#                                 'account.retention': (lambda self, cr, uid, ids, c={}: ids, ['retention_line_ids'], 11),
#                                 'account.retention.line': (_get_retention, ['tax_base', 'retention_percentage', 'retained_value',], 11),
#                                 }),
        'account_voucher_ids': fields.one2many('account.move.line', 'withhold_id', 'Retention'),
        'automatic': fields.boolean('Automatic?',),
        'period_id': fields.related('invoice_id','period_id', type='many2one', relation='account.period', string='Period', store=True), 
        'shop_id': fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
        'printer_id': fields.many2one('sri.printer.point', 'Printer Point', readonly=True, states={'draft':[('readonly',False)]}),
        #P.R: Required the authorization asociated depending if is purchase or sale
        'authorization_sri': fields.char('Authorization', readonly=True, states={'draft':[('readonly',False)]}, size=32),
        #P.R: Required in this format to generate the account moves using this lines
        'withhold_line_ids': fields.one2many('account.withhold.line', 'withhold_id', 'Withhold lines'),

    }
        
    _defaults = {
        'number': '',
        'transaction_type': _transaction_type,
        'state': lambda *a: 'draft',
                 }
    
    #Validacion básica del numero de retencion
    def check_retention_out(self,cr,uid,ids, context=None):
        cadena = '(\d{3})+\-(\d{3})+\-(\d{9})'
        for retention in self.browse(cr, uid, ids):
            ref = retention['number']
            if retention['number']:
                if re.match(cadena, ref):
                    return True
                else:
                    return False
            else:
                return True
            
    #_constraints = [(check_retention_out, _('The number of retention is incorrect, it must be like 001-00X-000XXXXXX, X is a number'),['number']),]
    
    _sql_constraints = [
                        ('withhold_number_purchase_uniq','unique(number_purchase)','There is another Withhold generated with this number, please verify'),
                        ]

    
    
#    TRESCLOUD - En este sprint no necesitamos esta funcionalidad, solo lo basico
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        retention = self.pool.get('account.retention').browse(cr, uid, ids, context)
        flag = context.get('invoice', False)
        unlink_ids = []
        for r in retention:
            if not flag:
                if r['state'] == 'draft':
                    unlink_ids.append(r['id'])
                else:
                    if r['state'] == 'canceled':
                        if r['transaction_type'] == 'sale':
                            unlink_ids.append(r['id'])
                        else:
                            raise osv.except_osv(_('Invalid action !'), _('Cannot delete retention(s) that are already assigned Number!'))
            else:
                unlink_ids.append(r['id'])
        return super(account_withhold, self).unlink(cr, uid, unlink_ids, context)
    
    def action_move_line_create(self, cr, uid, ids, context=None):

        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool.get('account.payment.term')
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False
        
        if context is None:
            context = {}
        
        withhold_id = False
        
        if 'withhold_id' in context:
            withhold_id = context['withhold_id']
            
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        seq_obj = self.pool.get('ir.sequence')
        
        for inv in self.pool.get('account.voucher').browse(cr, uid, ids, context=context):
        
            if inv.move_id:
                continue
            
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the voucher
            #TODO: se debe especificar el codigo de impuesto para la realizacion del informe de impuestos
            tax_code_obj = self.pool.get('account.tax.code')
            move_line = {}
            try:
                if context['tax']=='iva':
                    move_line = {
                        'name': inv.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': inv.account_id.id,
                        'move_id': move_id,
                        'journal_id': inv.journal_id.id,
                        'period_id': inv.period_id.id,
                        'partner_id': inv.partner_id.id,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                        'date': inv.date,
                        'date_maturity': inv.date_due,
                    }
                    
                elif context['tax']=='renta':
                    move_line = {
                        'name': inv.name or '/',
                        'debit': debit,
                        'credit': credit,
                        'account_id': inv.account_id.id,
                        'move_id': move_id,
                        'journal_id': inv.journal_id.id,
                        'period_id': inv.period_id.id,
                        'partner_id': inv.partner_id.id,
                        'currency_id': company_currency <> current_currency and  current_currency or False,
                        'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                        'date': inv.date,
                        'date_maturity': inv.date_due,
                    }

            except:
                raise osv.except_osv('Error!', _("The residual value of invoice is lower than total value of withholding"))
                    
            # Add the id of withhold
            if withhold_id:
                move_line['withhold_id'] = withhold_id

            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            elif inv.type == 'purchase':
                line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)

            for line in inv.line_ids:
                #create one move line per voucher line where amount is not 0.0
                if not line.amount:
                    continue
                #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
                if line.amount == line.amount_unreconciled:
                    amount = line.move_line_id.amount_residual #residual amount in company currency
                else:
                    amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                #print 'Por cada linea del voucher'
                #print move_line
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'

                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount

                if inv.tax_id and inv.type in ('sale', 'purchase'):
                    move_line.update({
                        'account_tax_id': inv.tax_id.id,
                    })
                if move_line.get('account_tax_id', False):
                    tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                    if not (tax_data.base_code_id and tax_data.tax_code_id):
                        raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
                    
                # Add the id of withhold
                if withhold_id:
                    move_line['withhold_id'] = withhold_id
                
                voucher_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [voucher_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)

            if not currency_pool.is_zero(cr, uid, inv.currency_id, line_total):
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    #account_id = inv.partner_id.property_account_receivable.id
                    account_id = inv.journal_id.default_debit_account_id.id
                else:
                    #account_id = inv.partner_id.property_account_payable.id
                    account_id = inv.journal_id.default_credit_account_id.id
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
                    #'currency_id': company_currency <> current_currency and current_currency or False,
                }
                    
                # Add the id of withhold
                if withhold_id:
                    move_line['withhold_id'] = withhold_id
                
                move_line_pool.create(cr, uid, move_line)
                #print 'asiento con desajuste'
                #print move_line
            self.pool.get('account.voucher').write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        return True
     
    # All actions exist because this work througth wizars and to prevent freezeing the screen 
    # the buttons call object function that execute the transition in workflow   
    def action_aprove(self, cr, uid, ids, context=None):
        #TRESCLOUD - No deberia depender del tipo de documento origen, remover sri.type.document o usar siempre el valor "factura"
        #document_obj = self.pool.get('sri.type.document')
        acc_vou_obj = self.pool.get('account.voucher')
        acc_vou_line_obj = self.pool.get('account.voucher.line')
        acc_move_line_obj = self.pool.get('account.move.line')
        ret_line_obj = self.pool.get('account.withhold.line')
        period_obj = self.pool.get('account.period')
        #sale_shop = self.pool.get('sales.shop').browse(cr, uid, 1, context=context)
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        journal_iva = company.journal_iva_id
        journal_ir = company.journal_ir_id
        
        if not journal_iva.default_debit_account_id:
            raise osv.except_osv('Error!', _("Iva Retention Journal doesn't have debit account assigned!, can't complete operation"))
        
        if not journal_ir.default_debit_account_id:
            raise osv.except_osv('Error!', _("IR Retention Journal doesn't have debit account assigned!, can't complete operation"))
        
        currency_pool = self.pool.get('res.currency')
        ret_obj = self.pool.get('account.retention')
        
        for ret in self.browse(cr, uid, ids, context=None):
            #lineas contables no conciliadas que pertenecen a la factura
            # Se requiere la suma de los haberes a cancelar
            total = 0
            sub_iva = 0
            sub_renta = 0
            
            for withhold in ret.withhold_line_ids:
                total = total + withhold.tax_amount
            
                if withhold.description == 'iva':
                    sub_iva = sub_iva + withhold.tax_amount
                
                if withhold.description == 'renta':
                    sub_renta = sub_renta + withhold.tax_amount
                
            # TRESCLOUD - TODO - days deberia seleccionarse en una seccion de configuracion contable
            day = datetime.timedelta(days=5)
            add_date = datetime.datetime(*time.strptime(ret.invoice_id.date_invoice,'%Y-%m-%d')[:5])+ day
            if ret.invoice_id.amount_total < total:
                raise osv.except_osv('Error!', _("Amount of retention is bigger than residual value of invoice, please verify"))
            if ret.creation_date < ret.invoice_id.date_invoice:
                raise osv.except_osv('Error!', _("The date of retention can not be least than the date of invoice"))
            if ret.creation_date > add_date.strftime('%Y-%m-%d'):
                # TRESCLOUD - TODO - solo debe botar un warning, queda atribucion del contador.
                raise osv.except_osv('Error!', _("The date of retention can not be more than 5 days from the date of the invoice"))
            if ((ret['transaction_type'])=='sale'):
                #P.R. puede emitirse mas de 1 retencion, una por el iva y otra por la renta
                #for retention in ret_obj.search(cr, uid, [('invoice_id.partner_id.id', '=', ret.invoice_id.partner_id.id), ('transaction_type','=','sale'), ('id','not in',tuple(ids))]):
                    #if ret_obj.browse(cr, uid, [retention,], context)[0].number_sale == ret.number_sale:
                        #raise osv.except_osv(_('Error!'), _("There is an retention with number %s of client %s") % (ret.number_sale, ret.invoice_id.partner_id.name))                        
                move_line_ids = acc_move_line_obj.search(cr, uid, [('invoice', '=', ret.invoice_id.id),('state','=','valid'), ('account_id.type', '=', 'receivable'), ('reconcile_id', '=', False)], context=context)
                #se asume que solo existira un movimiento sin conciliar por factura 
                #TODO ->>> Esto debe ser verificado mediante pruebas
                move_line = acc_move_line_obj.browse(cr, uid, move_line_ids, context)[0]
                #se comprueba que la factura se encuentre abierta
                if not ret.invoice_id.state == 'open':
                    raise osv.except_osv('Error!', "The invoice is not open, you cannot add a retention")
                #Se verifica que el residuo de la factura no sea superior a lo que se va a retener
                #TRESCLOUD - TODO discutir si se elimina esta condicion, los saldos a favor del cliente podrian conciliarse con otras facturas.
                #if ret.invoice_id.residual < ret.total:
                    #raise osv.except_osv('Error!', "The residual value of invoice is lower than total value of withholding")
                #Obtengo el periodo de la factura
                period=ret.invoice_id.period_id.id
                #creacion de vauchers de pago con retencion
                line_ids = ret_line_obj.search(cr, uid, [('withhold_id', '=', ret['id']),])
                lines = ret_line_obj.browse(cr, uid, line_ids, context)
                
                #variable que guarda los ids de los voucher que se crean para su posterior uso desde retencion
                vouchers = []
                #verifico que existan lineas de retencion
                if lines:
                    #creo la cabecera del voucher para las retenciones de iva
                    vals_vou_iva = {
                                'type':'receipt',
                                #periodo de la factura
                                'period_id': ret.invoice_id.period_id.id,
                                #fecha de la retencion
                                'date': ret.creation_date,
                                #el diario de iva de la compania
                                'journal_id': journal_iva.id,
                                #numero de retencion como referencia
                                'reference':_('RET CLI: %s') % ret.invoice_id.number,
                                #la cuenta de debido que va a registrar el impuesto
                                'account_id': journal_iva.default_debit_account_id.id,
                                'company_id' : company.id,
                                'amount': sub_iva,
                                'currency_id': ret.invoice_id.currency_id.id,
                                #'retention_id': ret.id,
                                'partner_id': ret.invoice_id.partner_id.id
                                
                    }
                    #creo la cabecera del voucher para las lineas de iva
                    voucher_iva = acc_vou_obj.create(cr, uid, vals_vou_iva, context)
                    vouchers.append(voucher_iva)
                    #creo la cabecera del voucher para las retenciones de renta
                    vals_vou_ir = {'type':'receipt',
                                #periodo de la factura
                                'period_id': ret.invoice_id.period_id.id,
                                #fecha de la retencion
                                'date': ret.creation_date,
                                #el diario de iva de la compania
                                'journal_id': journal_ir.id,
                                #numero de retencion como referencia
                                'reference':_('RET CLI: %s') % ret.invoice_id.number,
                                #la cuenta de debido que va a registrar el impuesto
                                'account_id': journal_ir.default_debit_account_id.id,
                                'company_id' : company.id,
                                'amount': sub_renta,
                                'currency_id': ret.invoice_id.currency_id.id,
                                #'retention_id': ret.id,
                                'partner_id': ret.invoice_id.partner_id.id
                    }
                    #creo la cabecera del voucher para las lineas de renta
                    voucher_ir = acc_vou_obj.create(cr, uid, vals_vou_ir, context)
                    vouchers.append(voucher_ir)
                    #recorro cada linea de retencion
                    #variables de control para verificar que existen lineas de cada tipo
                    renta = False
                    iva = False
                    for line in lines:
                        #verifico las lineas por tipo para seleccionar el diario correspondiente
                        if line.description == 'iva':
                            vals_vou__iva_line = {'voucher_id': voucher_iva,
                                             'move_line_id':move_line.id,
                                             'account_id':move_line.account_id.id,
                                             'amount':line.tax_amount,
                                             }
                            acc_vou_line_obj.create(cr, uid, vals_vou__iva_line, context)
                            #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                            iva = True
                            
                        if line.description == 'renta':
                            vals_vou_ir_line = {'voucher_id': voucher_ir,
                                             'move_line_id':move_line.id,
                                             'account_id':move_line.account_id.id,
                                             'amount':line.tax_amount,
                                             }
                            acc_vou_line_obj.create(cr, uid, vals_vou_ir_line, context)
                            #se cambia el valor de la variable ya que se encontro al menos una linea de retencion
                            renta = True
                    #se aprueba los voucher de rentencion, y se verifica que existan lineas
                    #acc_vou_obj.proforma_voucher(cr, uid, [voucher_iva, voucher_ir,], context)
                    if iva:
                        #por medio de la variable contexto se especifica que tipo de impuesto es del voucher
                        self.action_move_line_create(cr, uid, [voucher_iva,], context={'tax':'iva', 'withhold_id':ret.id})
                    #en caso de no existir lineas en el voucher se elimina el que se creo anteriormente
                    else:
                        acc_vou_obj.unlink(cr, uid,[voucher_iva,])
                        vouchers.remove(voucher_iva)
                    
                    if renta:
                        #por medio de la variable contexto se especifica que tipo de impuesto es del voucher
                        self.action_move_line_create(cr, uid, [voucher_ir,], context={'tax':'renta', 'withhold_id':ret.id})
                    #en caso de no existir lineas en el voucher se elimina el que se creo anteriormente
                    else:
                        acc_vou_obj.unlink(cr, uid,[voucher_ir,])
                        vouchers.remove(voucher_ir)
                    #print vouchers
                    #se cambia el estado de la retencion
                    if vouchers:
                        acc_vou_obj.write(cr, uid, vouchers, {'withhold_id':ret.id},context)
                    date_ret = None
                    if not ret.creation_date:
                        date_ret = time.strftime('%Y-%m-%d')
                    else:
                        date_ret = ret.creation_date
                    self.write(cr, uid, [ret.id,], { 'state': 'approved','creation_date': date_ret,'number':ret.number_sale, 'period_id': period}, context)
                else:
                    raise osv.except_osv('Error!', _("You can't aprove a retention without retention lines"))
            elif(ret['transaction_type']=='purchase'):
                if ret.invoice_id.period_id.id:
                    period=ret.invoice_id.period_id.id
                else:
                    user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
                    period = self.pool.get('account.period').search(cr, uid, [('date_start','<=',ret.invoice_id.date_invoice),('date_stop','>=',ret.invoice_id.date_invoice), ('company_id', '=', user.company_id.id)])
#                if not ret.authorization_purchase_id:
#                    raise osv.except_osv(_('Invalid action!'), _('Not exist authorization for the document, please check'))
#                if not ret.automatic:
#                    if not ret.number_purchase:
#                        raise osv.except_osv(_('Invalid action!'), _('Not exist number for the document, please check'))
#                    for doc in ret.authorization_purchase_id.type_document_ids:
#                        if doc.name=='withholding':
#                            document_obj.add_document(cr, uid, [doc.id,], context)
#                    self.write(cr, uid, [ret.id], {'number': ret.number_purchase, 'state': 'approved', 'period_id': period}, context)
                
                if not ret.number_purchase:
                    b = True
                    #vals_aut = self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'withholding')
#                    while b :
#                        number = self.pool.get('ir.sequence').get_id(cr, uid, vals_aut['sequence'])
#                        if not self.pool.get('account.retention').search(cr, uid, [('transaction_type','=','purchase'),('number','=',number),('id','not in',tuple(ids))],):
#                            b=False
#                    else:
                    number = ret.number
#                    for doc in ret.authorization_purchase_id.type_document_ids:
#                        if doc.name=='withholding':
#                            if doc.automatic:
#                                context['automatic'] = True
#                            document_obj.add_document(cr, uid, [doc.id,], context)
                    self.write(cr, uid, [ret.id], {'number': number, 'state': 'approved', 'period_id': period}, context)
        return True
    
    def action_cancel(self,cr,uid,ids,context=None):
        #document_obj = self.pool.get('sri.type.document')
        withhold = self.pool.get('account.retention').browse(cr, uid, ids, context)
        for ret in withhold:
            if ret.state == "draft":
                self.unlink(cr, uid, [ret.id,], context)
            else:
                #if ret.transaction_type == "automatic":
                    #for doc in ret.authorization_purchase.type_document_ids:
                        #if doc.name=='withholding':
                            #document_obj.rest_document(cr, uid, [doc.id,])
                    #self.pool.get('account.retention').write(cr, uid, [ret.id, ], {'state':'canceled'}, context)
                if ret.transaction_type == "sale":
                    vouchers = []
                    for vou in ret.account_voucher_ids:
                        vouchers.append(vou.id)
                    self.pool.get('account.voucher').cancel_voucher(cr, uid, vouchers, context)
                    self.pool.get('account.retention').write(cr, uid, [ret.id, ], {'state':'canceled'}, context)
                    #self.pool.get('account.retention').unlink(cr, uid, [ret.id, ], context)
        return True

    # Buttons to operate the workflow to prevet troubles whit double workflow
    def button_aprove(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_validate(uid, 'account.retention', id, 'approve_signal', cr)
        return True
    
    def button_cancel(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            self.pool.get('account.retention').write(cr, uid, id, {'state':'canceled'}, context)
            #wf_service.trg_validate(uid, 'account.retention', id, 'canceled_signal', cr)
        return True
    
    def button_set_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_delete(uid, 'account.retention', id, cr)
            wf_service.trg_create(uid, 'account.retention', id, cr)
        return True

account_withhold()
