import logging

from openerp.osv import fields, osv
from openerp import pooler
from openerp.tools.translate import _


class res_company(osv.Model):
    _inherit = 'res.company'
    _columns = {
        'contri_especial':fields.char('Special contributor', required=False, help='Resolution Special contributor'),
    }
res_company()        