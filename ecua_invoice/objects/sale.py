from osv import fields, osv

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def manual_invoice(self, cr, uid, ids, context=None):
        if context:
            partner=context.get('partner_id')  
        res = super(sale_order, self).manual_invoice(cr, uid, ids,context)
        inv_obj=self.pool.get('account.invoice')
        for invoice in inv_obj.browse(cr,uid,[res['res_id']]):
            invoice_address=invoice.partner_id.street 
            invoice_phone=invoice.partner_id.phone or invoice.partner_id.mobile
            inv_obj.write(cr,uid,res['res_id'],{'invoice_address':invoice_address,'invoice_phone':invoice_phone})
        user_obj=self.pool.get('res.users')
        printer_id=user_obj.browse(cr,uid,uid).printer_id
        if printer_id:
            inv_obj.write(cr,uid,res['res_id'],{'printer_id':printer_id.id})
        return res
sale_order()