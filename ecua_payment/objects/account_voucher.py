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
                }
    _defaults = {
        'responsible_id':lambda self, cr, uid, context: uid,
        }
         
    def proforma_voucher(self, cr, uid, ids, context=None):
        obj_voucher_self = self.browse(cr, uid, ids)
        obj_voucher_line = self.pool.get('account.voucher.line')
        for o in obj_voucher_self:
            for so_ids in obj_voucher_line.search(cr,uid,[('voucher_id','=',o.id)]):
                line = obj_voucher_line.browse(cr, uid, so_ids)
                "comparar para lanzar excepcion"
                
                if o.type in ['payment','receipt']:
                    if line.amount > line.amount_unreconciled: 
                        raise osv.except_osv(_('Error!'),
                                         _("$ %s > $ %s \n In the payment lines it is not possible to pay a value bigger the open balance, please correct the values") %(str(line.amount),str(line.amount_unreconciled)))
        return super(account_voucher, self).proforma_voucher(cr, uid, ids, context=None)                    
            
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