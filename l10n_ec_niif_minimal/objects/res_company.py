import logging

from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _


class res_company(osv.Model):
    _name = 'res.company'
    _inherit = ['res.company', 'mail.thread']
    _columns = {
        'special_tax_contributor_number':fields.char('Special Contributor Number', required=False, help='Special Contributors are designed by the Ecuadorian Tax Authority, the number is used in tax reporting', track_visibility='onchange'),
    }
res_company()        