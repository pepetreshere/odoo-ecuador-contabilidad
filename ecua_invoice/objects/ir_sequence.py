from osv import fields, osv
from osv.orm import setup_modifiers
from lxml import etree


class ir_sequence(osv.osv):
    _name = 'ir.sequence'
    _inherit = 'ir.sequence'

    def _freeze_field(self, name, fields, arch, freeze):
        """
        Alters, in-place, the res fields and arch to make a field.

        We check, beforehand, whether the field exists or not in the view.
        If the field does not exist, we do nothing. Otherwise we check for
          the nodes
        """
        freeze = int(freeze)
        if name in fields:
            fields[name]['readonly'] = freeze
            for node in arch.xpath("//field[@name='%s']" % name):
                setup_modifiers(node, fields[name])

    def _freeze_fields(self, context, fields, arch):
        """
        For each context variable, we try to fix the corresponding field in res
        """
        context = context or {}
        for key, value in context.iteritems():
            key = str(key) if not isinstance(key, (str, unicode)) else key
            if key.startswith('fix_') and isinstance(value, bool):
                self._freeze_field(key[4:], fields, arch, freeze=value)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        We support making the fields readonly. For that, we must pass a fix_xxx context variable evaluated as
          True or False. By passing False we make the field not-readonly. By passing True, we make it Readonly.
          In this context, "xxx" is the field name.
        """
        res = super(ir_sequence, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type,
                                                       context=context, toolbar=toolbar, submenu=submenu)
        fields = res['fields']
        arch = etree.XML(res['arch'])
        self._freeze_fields(context, fields, arch)
        res['arch'] = etree.tostring(arch)
        return res

ir_sequence()