# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 TRESCLOUD Cia Ltda (trescloud.com), Romero David
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp import netsvc
from tools.translate import _
import openerp.addons.decimal_precision as dp


class account_move_line(osv.osv):
    _inherit = "account.move.line"
    _name = 'account.move.line'

    def name_get(self, cr, uid, ids, context=None):
        """
        Genera un nombre basado en 3 cosas: nombre del movimiento, nombre de la factura asociada, nombre de asiento.
        """
        def _name(obj):
            # referenciamos invoice.name
            return ('%s %s%s' % (
                obj.move_id.name or '',
                obj.ref and ("(Referencia: %s)" % obj.ref) or '',
                obj.invoice and obj.invoice.name and (' (Factura: %s, a nombre de: %s)' % (obj.invoice.name, obj.invoice.partner_id.name)) or ''
            )).strip()
        return [(obj.id, _name(obj)) for obj in self.browse(cr, uid, ids, context)]

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        """
        Buscamos el nombre con el operador elegido, en los campos de nombre de factura, nombre de movimiento, y
          referencia del movimiento. Para esto, juntamos los criterios normales del search (los que recibimos como
          `args` y les concatenamos la siguiente lógica:

          Rompemos el nombre buscado en todas sus "palabras", separando por espacios, y contemplamos la posibilidad
            de que cada "palabra" aparezca en cualquiera de los tres campos: invoice.name, ref, y move_id.name.
        """
        name = str(name).strip()
        args_from_name = []

        if name:
            # la composicion de nombre entra solamente si hay nombre.
            # en caso contrario, delegamos la llamada en el padre.
            parts = str(name).split()
            args = list(args or ())
            for part in parts:
                """
                La idea de este bucle es que juntamos todos los criterios (serian como sub-dominios) que nos
                  armamos con cada "palabra" (tras haber roto el nombre en "palabras").

                Entonces por un lado concatenamos todos los posibles dominios, nos quedaría algo así como:

                para "123 hola": ['|', '|', ''|, ('invoice.name', operator, '123'),
                                                 ('invoice.internal_number', operator, '123'),
                                                 ('move_id.name', operator, '123'),
                                                 ('ref', operator, '123'),
                                  '|', '|', ''|, ('invoice.name', operator, 'hola'),
                                                 ('invoice.internal_number', operator, 'hola'),
                                                 ('move_id.name', operator, 'hola'),
                                                 ('ref', operator, 'hola')]

                Además de concatenar así estos criterios, del otro lado (por la izquierda del array) ponemos
                  operadores '|', uno por cada "palabra". Al finalizar el bucle, tenemos que POPear el primer
                  elemento del array (que será el de más a la izquierda: un '|') ya que si hay N terminos que
                  ponemos, deben haber N-1 operadores '|' entre ellos.

                Finalmente: tenemos la garantía de que a este bucle se ingresará al menos una vez, ya que al
                  comenzar este checkeo hicimos un .strip() y preguntamos si el nombre tenía "algo". Quiere
                  decir que tras invocarle .split() tendremos al menos un elemento para iterar, por lo que
                  al menos un '|' sobrante existirá.
                """
                args_from_name.extend(['|', '|', '|', '|',
                                       ('invoice.name', operator, part),
                                       ('invoice.internal_number', operator, part),
                                       ('invoice.partner_id.name', operator, part),
                                       ('move_id.name', operator, part),
                                       ('ref', operator, part)])
                args_from_name.insert(0, '|')
            args_from_name.pop(0)
            # Vaciamos el nombre para que no nos coma en el camino dependiendo del
            #   nombre (de eso ya nos encargamos nosotros), buscandolo dentro del 'name'
            #   del objeto (o el _rec_name respectivo). Para evitar esa condicion, DEBEMOS
            # PONER EL NAME EN VACIO.
            name = ''
        # Y ahora componemos de la siguiente manera: [a1, a2, ..., an, pa1, pa2, ..., pan]
        #   Ya que se exigirá que el search subyacente cumpla los criterios de args originales
        #   Y (&) los criterios de args_from_name posteriores.
        #
        # Para componernos esto nos basta simplemente con sumar ambas listas.
        return super(account_move_line, self).name_search(cr, uid, name, args + args_from_name, operator, limit=limit, context=context)


account_move_line()