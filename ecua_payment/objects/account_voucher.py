# coding=utf-8
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    _name = 'account.voucher'


    _columns = {
        'reference': fields.char('Ref #', size=64, readonly=True, states={'draft':[('readonly',False)]}, help="Is the number of document payment is file (eg footnote exit # 043)"),
        'name':fields.char('Memo', size=256, readonly=True, states={'draft':[('readonly',False)]}, help="Provides an explanation of the payment."),
        'responsible_id':fields.many2one('res.users', 'Responsible', change_default=1, help="Responsible for payment (the user who approves the payment)"),
        'comment': fields.char('Counterpart Comment', size=64, readonly=True, states={'draft': [('readonly', False)]}, ontracking=True)        
                }
    _defaults = {
        'responsible_id':lambda self, cr, uid, context: uid,
        'comment': '', #es mejor que el usuario escriba la razon del descuadre, asi tambien se limita el pago en exceso o el mal uso del modulo
        }
         
    def proforma_voucher(self, cr, uid, ids, context=None):
        """
        Before calling the base behavior, each line is compared for the vouchers.
        - They must have consistent values (regarding reconciles).
        - They must reference an account.move.line belonging to an account.move in Posted state.
        """
        for o in self.browse(cr, uid, ids, context=context):
            for line in o.line_cr_ids:
                "comparar para lanzar excepcion"

                if line.move_line_id == False:
                    raise osv.except_osv(_('Error!'), _(u'Al menos una línea no tiene una referencia válida a un '
                                                        u'apunte contable'))

                if line.move_line_id.move_id.state != 'posted':
                    raise osv.except_osv(_('Error!'), _(u'Al menos una línea del pago referencia a un apunte contable '
                                                        u'de un asiento no confirmado. Todas las líneas deben '
                                                        u'referenciar apuntes en asientos confirmados.'))

                if o.type in ['payment','receipt']:
                    if line.amount > line.amount_unreconciled: 
                        raise osv.except_osv(_('Error!'),
                                         _("$ %s > $ %s \n En las lineas de pago no es posible asignar un valor mayor al balance abierto, por favor corrija los valores") %(str(line.amount),str(line.amount_unreconciled)))
        return super(account_voucher, self).proforma_voucher(cr, uid, ids, context=None)                    


    def onchange_payment_option(self, cr, uid, ids, payment_option, journal_id):
        """ 
        Actualiza la cuenta contable para conciliacion del balance abierto de un voucher
        """
        res = {'value': {},'warning':{},'domain':{}}
        
        if payment_option in ['with_writeoff'] and journal_id:
            journal_obj = self.pool.get('account.journal')
            journal = journal_obj.browse(cr, uid, [journal_id], context=None)[0]
            writeoff_acc_id = False
            if journal.default_writeoff_acc_id:
                writeoff_acc_id = journal.default_writeoff_acc_id.id
            res['value'].update({'writeoff_acc_id': writeoff_acc_id})
        else:
            res['value'].update({'writeoff_acc_id': False})
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        '''
        Si al cambiar el payment_option atualizamos las cuentas acorde al diario,
        entonces debemos tambien actualizarlas cuando cambie el diario.
        Por facilidad se ha programado que al cambiar el diario el payment_option se cambie a without_writeoff
        '''
        res = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if not res:
            res = {}
        if not res.get('value',False):
            res['value'] = {}

        res['value'].update({'payment_option': 'without_writeoff',
                             'writeoff_acc_id': False,
                             })
        return res
            
    def button_print_pay_voucher(self, cr, uid, ids, context=None):
        #TODO: Hacer que el boton retorne el reporte impreso
        #self.print_document_type(cr, uid, ids, context=context)
        self.button_proforma_voucher(cr, uid, ids, context=context)

        return True;
                
account_voucher()


# class account_voucher_line(osv.osv):
#     _inherit = 'account.voucher.line'
#     _name = 'account.voucher.line'
#     
#     def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, context=None):
#         '''
#         Lanzamos advertencias para guiar al usuario en el correcto uso del sistema
#         '''
#         res = super(account_voucher_line, self).onchange_amount(cr, uid, ids, amount, amount_unreconciled, context=None)
#         return res
#         res['warning'] = {}
#         if amount > amount_unreconciled: 
#             res['warning'] = {'title': _('Warning!'), 
#                               'message': _("Are you sure? In this payment line the Amount is bigger than the Open Amount, this is unusual unless for example you are forgiving some cents missmatch in which case dont forget to make a write-off for the difference in the bottom of the form (Example to sent 2 cents to the account 430500 OTHER INCOMES)")}
#         return res
#     
# account_voucher_line()