from osv import fields, osv
from osv.orm import setup_modifiers
from lxml import etree


class ir_sequence(osv.osv):
    _name = 'ir.sequence'
    _inherit = 'ir.sequence'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        We set the field to readonly depending on the passed flags. This means:
           * We must specify to fix the sequence type (fixed_sequence_type=True).
           * We must specify a default value for the "code" (default_code=my.custom.seq.code).

        This only applies to context (e.g. a context node in a ir.action.act_window object, or a <field /> tag for a
           relational field to this object, with a context with these values).
        """
        res = super(ir_sequence, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
                                                       context=context, toolbar=toolbar, submenu=submenu)
        context = context or {}
        is_fixed = context.get('fixed_sequence_type', False) and bool(context.get('default_code', False))
        if is_fixed and 'code' in res['fields']:
            res['fields']['code']['readonly'] = 1

            arch = etree.XML(res['arch'])
            for node in arch.xpath("//field[@name='code']"):
                node.set('readonly', "1")
                setup_modifiers(node, res['fields']['code'])
            res['arch'] = etree.tostring(arch)

        return res

ir_sequence()