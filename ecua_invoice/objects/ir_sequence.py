from osv import fields, osv
from osv.orm import setup_modifiers
from lxml import etree


class ir_sequence(osv.osv):
    _name = 'ir.sequence'
    _inherit = ['ir.sequence', 'trait.context.for.fields']
    _auto = False
ir_sequence()