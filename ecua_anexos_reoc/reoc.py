# -*- coding: UTF-8 -*- #
#########################################################################
# Copyright (C) 2011  Christopher Ormaza, Ecuadorenlinea.net            #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields,osv
import decimal_precision as dp
from tools.translate import _
from tools import config
import time
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
import sys
import base64

class sri_reoc(osv.osv):
    mes_lista=[]
    
    def indent(self,elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


    
    def act_cancelar(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    
    def tipo_identificacion_compra(self,type):
        if type=='ruc':
            return '01'
        elif type=='cedula':
            return '02'
        
    def formato_numero(self,valor,number_of_zeros=2):
        tup= valor.split('.')
        if len(tup[1])== 1:
            res = valor
            for n in range(number_of_zeros - 1):
                res += "0"
        return valor
    
    def valor(self,tup):
        if tup:
            return tup[0]
        else:
            return 0.0
    
    def get_base(self, ret):
        base_no_iva = 0.0
        base_iva_0 = 0.0
        base_iva_12 = 0.0
        lines_with_ret_code = []
        for line in ret.invoice_id.invoice_line:
            for tax in line.invoice_line_tax_id:
                if tax.base_code_id.code == ret.tax_id.code:
                    lines_with_ret_code.append(line)
        for line in lines_with_ret_code:
            for tax in line.invoice_line_tax_id:
                if tax.type_ec == 'iva' and tax.amount == 0:
                     base_iva_0 += line.price_subtotal
                     break
                if tax.type_ec == 'iva' and tax.amount == 0.12:
                     base_iva_12 += line.price_subtotal
                     break
	diff = abs(base_iva_0 + base_iva_12 - ret.tax_base) >= (ret.invoice_id.currency_id.rounding/2.0)
        if diff and abs(base_iva_0 + base_iva_12 - ret.tax_base) > 0.01:
            base_no_iva = ret.tax_base - (base_iva_0 + base_iva_12)
        return base_iva_0, base_iva_12, base_no_iva
    
    def generate_xml(self, cr, uid, ids, context=None):
        root = ''
        for anexo in self.browse(cr, uid, ids, context=context):
           invoice_compras_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('foreign','=',False),('type','=','in_invoice'),('state','in',('open','paid')),])
           credit_note_purchase_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','in_refund'),('foreign','=',False),('state','in',('open','paid')),])
           invoice_compras = self.pool.get('account.invoice').browse(cr, uid, invoice_compras_ids, context)
           credit_note_purchases = self.pool.get('account.invoice').browse(cr, uid, credit_note_purchase_ids, context)
           company = self.pool.get('res.users').browse(cr, uid, [uid,], context)[0].company_id.partner_id
           root = Element("reoc")
           mes= anexo['period_id']['name']
           self.mes_lista=mes.split('/')
           SubElement(root,"numeroRuc").text=company.ref
           SubElement(root,"anio").text=anexo['fiscalyear_id']['name']
           SubElement(root,"mes").text=self.mes_lista[0]
           if invoice_compras:            
                compras = SubElement(root,"compras")
                for inv in invoice_compras:
                    tipoComprobante = "01"
                    autorizacion = inv.authorization_purchase_id
                    if inv.liquidation:
                        tipoComprobante = "03"
                        autorizacion = inv.authorization_liquidation.number
                    numero_factura=inv.number.split('-')
                    fecha=(str(inv.date_invoice))
                    fecha=fecha.split('-')
                    detalle = SubElement(compras,"detalleCompras")
                    SubElement(detalle, "tpIdProv").text = self.tipo_identificacion_compra(inv.partner_id.type_ref)
                    SubElement(detalle, "idProv").text = inv.partner_id.ref
                    SubElement(detalle, "tipoComp").text = tipoComprobante
                    SubElement(detalle, "aut").text = autorizacion
                    SubElement(detalle, "estab").text = numero_factura[0]
                    SubElement(detalle, "ptoEmi").text = numero_factura[1]
                    SubElement(detalle, "sec").text = numero_factura[2]
                    SubElement(detalle, "fechaEmiCom").text = fecha[2]+"/"+fecha[1]+"/"+fecha[0]
                    retencion = SubElement(detalle, "air")
                    if inv.retention_line_ids:
                        for ret in inv.retention_line_ids:
                            if ret.description == 'renta':
                                detalle_retencion = SubElement(retencion, "detalleAir")
                                SubElement(detalle_retencion, "codRetAir").text = ret.tax_id.code
                                SubElement(detalle_retencion, "porcentaje").text = self.formato_numero(str(ret.retention_percentage))
                                base_iva_0, base_iva_12, base_no_iva = self.get_base(ret)
                                SubElement(detalle_retencion, "base0").text = self.formato_numero(str(base_iva_0))
                                SubElement(detalle_retencion, "baseGrav").text = self.formato_numero(str(base_iva_12))
                                SubElement(detalle_retencion, "baseNoGrav").text = self.formato_numero(str(base_no_iva))
                                SubElement(detalle_retencion, "valRetAir").text = self.formato_numero(str(ret.retained_value),1)
                    if inv.retention_ids:
                        fecha_ret=(str(ret.creation_date))
                        fecha_ret=fecha_ret.split('-')
                        ret = inv.retention_ids[0]
                        numero_retencion=ret.number.split('-')
                        SubElement(detalle, "autRet").text = ret.authorization_purchase_id.number
                        SubElement(detalle, "estabRet").text = numero_retencion[0]
                        SubElement(detalle, "ptoEmiRet").text = numero_retencion[1]
                        SubElement(detalle, "secRet").text = numero_retencion[2]
                        SubElement(detalle, "fechaEmiRet").text = fecha_ret[2]+"/"+fecha_ret[1]+"/"+fecha_ret[0]
           #credit notes
                for inv in credit_note_purchases:
                    tipoComprobante = "04"
                    autorizacion = inv.authorization_credit_note_purchase
                    numero_factura=inv.number.split('-')
                    fecha=(str(inv.date_invoice))
                    fecha=fecha.split('-')
                    detalle = SubElement(compras,"detalleCompras")
                    SubElement(detalle, "tpIdProv").text = self.tipo_identificacion_compra(inv.partner_id.type_ref)
                    SubElement(detalle, "idProv").text = inv.partner_id.ref
                    SubElement(detalle, "tipoComp").text = tipoComprobante
                    SubElement(detalle, "aut").text = autorizacion
                    SubElement(detalle, "estab").text = numero_factura[0]
                    SubElement(detalle, "ptoEmi").text = numero_factura[1]
                    SubElement(detalle, "sec").text = numero_factura[2]
                    SubElement(detalle, "fechaEmiCom").text = fecha[2]+"/"+fecha[1]+"/"+fecha[0]
                    retencion = SubElement(detalle, "air")
                    if inv.retention_line_ids:
                        for ret in inv.retention_line_ids:
                            if ret.description == 'renta':
                                detalle_retencion = SubElement(retencion, "detalleAir")
                                SubElement(detalle_retencion, "codRetAir").text = ret.tax_id.code
                                SubElement(detalle_retencion, "porcentaje").text = self.formato_numero(str(ret.retention_percentage))
                                base_iva_0, base_iva_12, base_no_iva = self.get_base(ret)
                                SubElement(detalle_retencion, "base0").text = self.formato_numero(str(base_iva_0))
                                SubElement(detalle_retencion, "baseGrav").text = self.formato_numero(str(base_iva_12))
                                SubElement(detalle_retencion, "baseNoGrav").text = self.formato_numero(str(base_no_iva))
                                SubElement(detalle_retencion, "valRetAir").text = self.formato_numero(str(ret.retained_value),1)
                    if inv.retention_ids:
                        fecha_ret=(str(ret.creation_date))
                        fecha_ret=fecha_ret.split('-')
                        ret = inv.retention_ids[0]
                        numero_retencion=ret.number.split('-')
                        SubElement(detalle, "autRet").text = ret.authorization_purchase_id.number
                        SubElement(detalle, "estabRet").text = numero_retencion[0]
                        SubElement(detalle, "ptoEmiRet").text = numero_retencion[1]
                        SubElement(detalle, "secRet").text = numero_retencion[2]
                        SubElement(detalle, "fechaEmiRet").text = fecha_ret[2]+"/"+fecha_ret[1]+"/"+fecha_ret[0]                   
        self.indent(root)
        return tostring(root,encoding="ISO-8859-1")
    
    
    def act_export(self, cr, uid, ids, context={}):
        this = self.browse(cr, uid, ids)[0]
        root = self.generate_xml(cr,uid,ids)
        this.name = "REOC"+self.mes_lista[0]+self.mes_lista[1]+".xml"
        #self._write_attachment(cr,uid,ids,root,context)
        out=base64.encodestring(root)
        return self.write(cr, uid, ids, {'data':out, 'name':this.name, 'state': 'get'}, context=context)
        
        
    _name = 'sri.reoc'
    
    _columns = {
                'name':fields.char('name', size=20, readonly=True), 
                'fiscalyear_id':fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
                'period_id':fields.many2one('account.period', 'Period', required=True),
                'data':fields.binary('File', readonly=True),
                'state':fields.selection([
                ('choose','Choose'),
                ('get','Get'),
                ],  'state', required=True, readonly=True),
                 }
    _defaults = {
                 'state': lambda *a: 'choose'
                 }
    
sri_reoc()
