from osv import fields, osv
class res_users(osv.Model):
    _inherit = 'res.users'
    _columns = {
        'printer_id':fields.many2one('sri.printer.point', 'Default Printer Point'),
    }
res_users()