from openerp.osv import osv
from openerp.tools.translate import _

class invoice(osv.osv):
    _inherit = 'account.invoice'
    def button_print_pay_voucher(self, cr, uid, ids, context=None):
        #self.print_document_type(cr, uid, ids, context=context)
        self.button_proforma_voucher(cr, uid, ids, context=context)

        return True;
invoice()        