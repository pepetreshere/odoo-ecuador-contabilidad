# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                  
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  
########################################################################

from osv import fields,osv
import decimal_precision as dp
from tools.translate import _
from tools import config
import time
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
import sys
import base64

class sri_ats(osv.osv_memory):
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

    def tipo_identificacion_compra(self,type):
        if type=='ruc':
            return '01'
        elif type=='cedula':
            return '02'
        
        
    def tipo_identificacion_venta(self,type):
        if type=='ruc':
            return '04'
        elif type=='cedula':
            return '05'
        elif type=='consumidor':
            return '07'
        
    def formato_numero(self,valor):
        tup= valor.split('.')
        if len(tup[1])== 1:
            return valor+"0"
        return valor
    
    def valor(self,tup):
        if tup:
            return tup[0]
        else:
            return 0.0
    
    def act_cancelar(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }
    
    def act_destroy(self, *args):
        return {'type':'ir.actions.act_window_close' }
    
    def generate_xml(self, cr, uid, ids, context=None):
        root = ''
        for anexo in self.browse(cr, uid, ids, context=context):
            #Facturas en compras que pertenecen al periodo
            invoice_compras_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','in_invoice'),('state','in',('open','paid')),])
            invoice_compras = self.pool.get('account.invoice').browse(cr, uid, invoice_compras_ids, context)
            #Facturas en ventas que pertenecen al periodo
            invoice_ventas_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','out_invoice'),('state','in',('open','paid')),])
            invoice_ventas = self.pool.get('account.invoice').browse(cr, uid, invoice_ventas_ids, context)
            #Notas de Credito en ventas que pertenecen al periodo
            refund_ventas_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','out_refund'),('state','in',('open','paid')),])
            refund_ventas = self.pool.get('account.invoice').browse(cr, uid, refund_ventas_ids, context)
            #Notas de Credito en compras que pertenecen al periodo
            refund_compras_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','in_refund'),('state','in',('open','paid')),])
            refund_compras = self.pool.get('account.invoice').browse(cr, uid, refund_compras_ids, context)
            #Facturas de Ventas Canceladas
            invoice_canceled_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','out_invoice'),('state','=','cancel'),])
            invoice_canceled = self.pool.get('account.invoice').browse(cr, uid, invoice_canceled_ids, context)
            #Notas de Credito en Ventas Canceladas
            credit_note_canceled_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','out_refund'),('state','=','cancel'),])
            credit_note_canceled = self.pool.get('account.invoice').browse(cr, uid, credit_note_canceled_ids, context)
            #Liquidacion de Compras Canceladas
            liquidation_canceled_ids = self.pool.get('account.invoice').search(cr, uid, [('period_id.id','=',anexo['period_id']['id']),('type','=','in_invoice'),('state','=','cancel'),('liquidation','=',True)])
            liquidation_canceled = self.pool.get('account.invoice').browse(cr, uid, liquidation_canceled_ids, context)

            company = self.pool.get('res.users').browse(cr, uid, [uid,], context)[0].company_id.partner_id
            root = Element("iva")
            mes= anexo['period_id']['name']
            self.mes_lista=mes.split('/')
            SubElement(root,"numeroRuc").text=company.ref
            SubElement(root,"razonSocial").text=company.name
            SubElement(root,"anio").text=anexo['fiscalyear_id']['name']
            SubElement(root,"mes").text=self.mes_lista[0]
            
            #Se verifica que existan facturas en compras o Notas de Credito
            if invoice_compras or refund_compras:            
                compras = SubElement(root,"compras")
                for inv in invoice_compras:
                    numero_factura=inv.number.split('-')
                    fecha_emision=(str(inv.date_invoice))
                    fecha_emision=fecha_emision.split('-')
                    fecha_registro=(str(inv.create_date))
                    fecha_registro=fecha_registro.split(' ')
                    fecha_registro=fecha_emision
#                    fecha_registro=fecha_registro[0].split('-')
                    detalle = SubElement(compras,"detalleCompras")
                    if inv.tax_support_id.code or False:
                        SubElement(detalle, "codSustento").text = inv.tax_support_id.code
                    SubElement(detalle, "tpIdProv").text = self.tipo_identificacion_compra(inv.partner_id.type_ref)
                    SubElement(detalle, "idProv").text = inv.partner_id.ref
                    #Al escoger el voucher type se agregan tambien las liquidaciones de compras
                    SubElement(detalle, "tipoComprobante").text = inv.voucher_type_id.code
                    SubElement(detalle, "fechaRegistro").text = fecha_registro[2]+"/"+fecha_registro[1]+"/"+fecha_registro[0]
                    SubElement(detalle, "establecimiento").text = numero_factura[0]
                    SubElement(detalle, "puntoEmision").text = numero_factura[1]
                    SubElement(detalle, "secuencial").text = numero_factura[2]
                    SubElement(detalle, "fechaEmision").text = fecha_emision[2]+"/"+fecha_emision[1]+"/"+fecha_emision[0]
                    if inv.liquidation:
                        SubElement(detalle, "autorizacion").text = inv.authorization_liquidation.number
                    else:
                        SubElement(detalle, "autorizacion").text = inv.authorization_supplier_purchase_id.number
                    #CHECK: SE DEBE VERIFICAR QUE CADA LINEA DE FACTURA TENGA UN IMPUESTO AL MENOS, EN CASO DE NO TENER SE CONSIDERA COMO BASE QUE NO APLICA IVA
                    SubElement(detalle, "baseNoGraIva").text = "0.00"
                    SubElement(detalle, "baseImponible").text = self.formato_numero(str(self.valor([n.base for n in inv.tax_line if n.base_code_id.code == "517"])))
                    SubElement(detalle, "baseImpGrav").text = self.formato_numero(str(self.valor([n.base for n in inv.tax_line if n.base_code_id.code in ("511","512","513","514","515")])))
                    SubElement(detalle, "montoIce").text = self.formato_numero(str(inv.total_ice)) or "0.00"
                    SubElement(detalle, "montoIva").text = self.formato_numero(str(inv.total_iva)) or "0.00"
                    SubElement(detalle, "valorRetBienes").text = self.formato_numero(str(self.valor([abs(n.tax_amount) for n in inv.tax_line if n.tax_code_id.code == "721"])))
                    SubElement(detalle, "valorRetServicios").text = self.formato_numero(str(self.valor([abs(n.tax_amount) for n in inv.tax_line if n.tax_code_id.code == "723"])))
                    SubElement(detalle, "valRetServ100").text = self.formato_numero(str(self.valor([abs(n.tax_amount) for n in inv.tax_line if n.tax_code_id.code == "725"])))
                    #Retenciones en COmpras
                    retencion = SubElement(detalle, "air")
                    if inv.retention_line_ids:
                        for ret in inv.retention_line_ids:
                            if ret.description == 'renta':
                                detalle_retencion = SubElement(retencion, "detalleAir")
                                SubElement(detalle_retencion, "codRetAir").text = ret.tax_id.code
                                SubElement(detalle_retencion, "baseImpAir").text = self.formato_numero(str(abs(ret.tax_base)))
                                SubElement(detalle_retencion, "porcentajeAir").text = self.formato_numero(str(abs(ret.retention_percentage)))
                                SubElement(detalle_retencion, "valRetAir").text = self.formato_numero(str(abs(ret.retained_value)))
                    if inv.retention_ids:
                        fecha_ret=(str(ret.creation_date))
                        fecha_ret=fecha_ret.split('-')
                        ret = inv.retention_ids[0]
                        numero_retencion=ret.number.split('-')
                        SubElement(detalle, "estabRetencion1").text = numero_retencion[0]
                        SubElement(detalle, "ptoEmiRetencion1").text = numero_retencion[1]
                        SubElement(detalle, "secRetencion1").text = numero_retencion[2]
                        SubElement(detalle, "autRetencion1").text = ret.authorization_purchase_id.number
                        SubElement(detalle, "fechaEmiRet1").text = fecha_ret[2]+"/"+fecha_ret[1]+"/"+fecha_ret[0]
                        SubElement(detalle, "estabRetencion2").text = "000"
                        SubElement(detalle, "ptoEmiRetencion2").text = "000"
                        SubElement(detalle, "secRetencion2").text = "0"
                        SubElement(detalle, "autRetencion2").text = "000"
                        SubElement(detalle, "fechaEmiRet2").text = "00/00/0000"
                    else:
                        SubElement(detalle, "estabRetencion1").text = "000"
                        SubElement(detalle, "ptoEmiRetencion1").text = "000"
                        SubElement(detalle, "secRetencion1").text = "0"
                        SubElement(detalle, "autRetencion1").text = "000"
                        SubElement(detalle, "fechaEmiRet1").text = "00/00/0000"
                        SubElement(detalle, "estabRetencion2").text = "000"
                        SubElement(detalle, "ptoEmiRetencion2").text = "000"
                        SubElement(detalle, "secRetencion2").text = "0"
                        SubElement(detalle, "autRetencion2").text = "000"
                        SubElement(detalle, "fechaEmiRet2").text = "00/00/0000"
                    SubElement(detalle, "docModificado").text = "0"
                    SubElement(detalle, "estabModificado").text = "000"
                    SubElement(detalle, "ptoEmiModificado").text = "000"
                    SubElement(detalle, "secModificado").text = "0"
                    SubElement(detalle, "autModificado").text = "000"
            
            #Notas de Credito de Proveedores
                for inv in refund_compras:
                    numero_factura = inv.number.split('-')
                    numero_nota_credito = inv.invoice_rectification_id.split('-')
                    fecha_emision=(str(inv.date_invoice))
                    fecha_emision=fecha_emision.split('-')
                    fecha_registro=(str(inv.create_date))
                    fecha_registro=fecha_registro.split(' ')
                    fecha_registro=fecha_emision
#                    fecha_registro=fecha_registro[0].split('-')
                    detalle = SubElement(compras,"detalleCompras")
                    if inv.tax_support_id.code or False:
                        SubElement(detalle, "codSustento").text = inv.tax_support_id.code
                    SubElement(detalle, "tpIdProv").text = self.tipo_identificacion_compra(inv.partner_id.type_ref)
                    SubElement(detalle, "idProv").text = inv.partner_id.ref
                    SubElement(detalle, "tipoComprobante").text = inv.voucher_type_id.code
                    SubElement(detalle, "fechaRegistro").text = fecha_registro[2]+"/"+fecha_registro[1]+"/"+fecha_registro[0]
                    SubElement(detalle, "establecimiento").text = numero_factura[0]
                    SubElement(detalle, "puntoEmision").text = numero_factura[1]
                    SubElement(detalle, "secuencial").text = numero_factura[2]
                    SubElement(detalle, "fechaEmision").text = fecha_emision[2]+"/"+fecha_emision[1]+"/"+fecha_emision[0]
                    SubElement(detalle, "autorizacion").text = inv.authorization_credit_note_purchase_id.number
                    #CHECK: SE DEBE VERIFICAR QUE CADA LINEA DE FACTURA TENGA UN IMPUESTO AL MENOS, EN CASO DE NO TENER SE CONSIDERA COMO BASE QUE NO APLICA IVA
                    SubElement(detalle, "baseNoGraIva").text = "0.00"
                    SubElement(detalle, "baseImponible").text = self.formato_numero(str(self.valor([n.base for n in inv.tax_line if n.base_code_id.code == "517"])))
                    SubElement(detalle, "baseImpGrav").text = self.formato_numero(str(self.valor([n.base for n in inv.tax_line if n.base_code_id.code in ("511","512","513","514","515")])))
                    SubElement(detalle, "montoIce").text = self.formato_numero(str(inv.total_ice)) or "0.00"
                    SubElement(detalle, "montoIva").text = self.formato_numero(str(inv.total_iva)) or "0.00"
                    SubElement(detalle, "valorRetBienes").text = self.formato_numero(str(self.valor([abs(n.tax_amount) for n in inv.tax_line if n.tax_code_id.code == "721"])))
                    SubElement(detalle, "valorRetServicios").text = self.formato_numero(str(self.valor([abs(n.tax_amount) for n in inv.tax_line if n.tax_code_id.code == "723"])))
                    SubElement(detalle, "valRetServ100").text = self.formato_numero(str(self.valor([abs(n.tax_amount) for n in inv.tax_line if n.tax_code_id.code == "725"])))
                    retencion = SubElement(detalle, "air")
                    if inv.retention_line_ids:
                        for ret in inv.retention_line_ids:
                            if ret.description == 'renta':
                                detalle_retencion = SubElement(retencion, "detalleAir")
                                SubElement(detalle_retencion, "codRetAir").text = ret.tax_id.code
                                SubElement(detalle_retencion, "baseImpAir").text = self.formato_numero(str(abs(ret.tax_base)))
                                SubElement(detalle_retencion, "porcentajeAir").text = self.formato_numero(str(abs(ret.retention_percentage)))
                                SubElement(detalle_retencion, "valRetAir").text = self.formato_numero(str(abs(ret.retained_value)))
                    if inv.retention_ids:
                        fecha_ret=(str(ret.creation_date))
                        fecha_ret=fecha_ret.split('-')
                        ret = inv.retention_ids[0]
                        numero_retencion=ret.number.split('-')
                        SubElement(detalle, "estabRetencion1").text = numero_retencion[0]
                        SubElement(detalle, "ptoEmiRetencion1").text = numero_retencion[1]
                        SubElement(detalle, "secRetencion1").text = numero_retencion[2]
                        SubElement(detalle, "autRetencion1").text = ret.authorization_purchase_id.number
                        SubElement(detalle, "fechaEmiRet1").text = fecha_ret[2]+"/"+fecha_ret[1]+"/"+fecha_ret[0]
                        SubElement(detalle, "estabRetencion2").text = "000"
                        SubElement(detalle, "ptoEmiRetencion2").text = "000"
                        SubElement(detalle, "secRetencion2").text = "0"
                        SubElement(detalle, "autRetencion2").text = "000"
                        SubElement(detalle, "fechaEmiRet2").text = "00/00/0000"
                    else:
                        SubElement(detalle, "estabRetencion1").text = "000"
                        SubElement(detalle, "ptoEmiRetencion1").text = "000"
                        SubElement(detalle, "secRetencion1").text = "0"
                        SubElement(detalle, "autRetencion1").text = "0"
                        SubElement(detalle, "fechaEmiRet1").text = "00/00/0000"
                        SubElement(detalle, "estabRetencion2").text = "000"
                        SubElement(detalle, "ptoEmiRetencion2").text = "000"
                        SubElement(detalle, "secRetencion2").text = "0"
                        SubElement(detalle, "autRetencion2").text = "000"
                        SubElement(detalle, "fechaEmiRet2").text = "00/00/0000"
                                                
                    SubElement(detalle, "docModificado").text = inv.invoice_rectification_id.voucher_type_id.code
                    SubElement(detalle, "estabModificado").text = numero_nota_credito[0]
                    SubElement(detalle, "ptoEmiModificado").text = numero_nota_credito[1]
                    SubElement(detalle, "secModificado").text = numero_nota_credito[2]
                    SubElement(detalle, "autModificado").text = inv.invoice_rectification_id
            
            #TODO: Liquidacion de Compras
            #TODO: NOTAS DE CREDITO EN VENTAS
            else:
                compras = SubElement(root,"compras")
            #FACTURAS DE VENTAS
            if invoice_ventas:
                list_client = []
                for inv in invoice_ventas:
                    client_id = self.pool.get('res.partner').search(cr, uid, [('id','=',inv['partner_id']['id']),])
                    if not client_id[0] in list_client:
                        list_client.append(client_id[0])
                cliente = self.pool.get('res.partner').browse(cr, uid, list_client, context)
                ventas = SubElement(root,"ventas")
                for cli in cliente:
                    #Facturas en Ventas
                    num_comprobantes_facturas=0
                    base=0.0
                    base_0=0.0
                    iva=0.0
                    iva_ret=0.0
                    renta_ret=0.0
                    inv_vent_ids= self.pool.get('account.invoice').search(cr, uid, [('partner_id.id','=',cli['id']),('period_id.id','=',anexo['period_id']['id']),('type','=','out_invoice'),('state','in',('open','paid')),])
                    num_comprobantes_facturas= len(inv_vent_ids)
                    inv_ventas = self.pool.get('account.invoice').browse(cr, uid, inv_vent_ids, context)
                    for inv in inv_ventas:
                        base=base+self.valor([n.base for n in inv.tax_line if n.base_code_id.code in ("411",)])
                        base_0=base+self.valor([n.base for n in inv.tax_line if n.base_code_id.code in ("415","416","413","414")])
                        iva=iva+self.valor([n.amount for n in inv.tax_line if n.tax_code_id.code in ("421",)])
                        if inv.retention_ids:
                            for ret in inv.retention_ids:
                                iva_ret=iva_ret+ret.total_iva
                                renta_ret=renta_ret+ret.total_renta
                    if inv_ventas:
                        detalle = SubElement(ventas,"detalleVentas")
                        SubElement(detalle, "tpIdCliente").text = self.tipo_identificacion_venta(cli.type_ref)
                        SubElement(detalle, "idCliente").text = cli.ref
                        SubElement(detalle, "tipoComprobante").text = "18"
                        SubElement(detalle, "numeroComprobantes").text = str(num_comprobantes_facturas)
                        SubElement(detalle, "baseNoGraIva").text = "0.00"
                        SubElement(detalle, "baseImponible").text = self.formato_numero(str(base_0))
                        SubElement(detalle, "baseImpGrav").text = self.formato_numero(str(base))
                        SubElement(detalle, "montoIva").text = self.formato_numero(str(iva))
                        SubElement(detalle, "valorRetIva").text = self.formato_numero(str(iva_ret))
                        SubElement(detalle, "valorRetRenta").text = self.formato_numero(str(renta_ret))

                    #Notas de Credito
                    num_comprobantes_nc=0
                    base_nc=0.0
                    base_nc_0=0.0
                    iva_nc=0.0
                    iva_ret_nc=0.0
                    renta_ret_nc=0.0
                    inv_notas_credito_ids= self.pool.get('account.invoice').search(cr, uid, [('partner_id.id','=',cli['id']),('period_id.id','=',anexo['period_id']['id']),('type','=','out_refund'),('state','in',('open','paid')),])
                    num_comprobantes_facturas= len(inv_notas_credito_ids)
                    inv_notas_credito = self.pool.get('account.invoice').browse(cr, uid, inv_notas_credito_ids, context)
                    for inv in inv_notas_credito:
                        base_nc=base+self.valor([n.base for n in inv.tax_line if n.base_code_id.code in ("411")])
                        base_nc_0=base+self.valor([n.base for n in inv.tax_line if n.base_code_id.code in ("415","416","413","414")])
                        iva_nc=iva+self.valor([n.amount for n in inv.tax_line if n.tax_code_id.code in ("421")])
                        if inv.retention_ids:
                            for ret in inv.retention_ids:
                                iva_ret_nc=iva_ret+ret.total_iva
                                renta_ret_nc=renta_ret+ret.total_renta
                    if inv_notas_credito:
                        detalle = SubElement(ventas,"detalleVentas")
                        SubElement(detalle, "tpIdCliente").text = self.tipo_identificacion_venta(cli.type_ref)
                        SubElement(detalle, "idCliente").text = cli.ref
                        SubElement(detalle, "tipoComprobante").text = "04"
                        SubElement(detalle, "numeroComprobantes").text = str(num_comprobantes_nc)
                        SubElement(detalle, "baseNoGraIva").text = "0.00"
                        SubElement(detalle, "baseImponible").text = self.formato_numero(str(base_nc_0))
                        SubElement(detalle, "baseImpGrav").text = self.formato_numero(str(base_nc))
                        SubElement(detalle, "montoIva").text = self.formato_numero(str(iva_nc))
                        SubElement(detalle, "valorRetIva").text = self.formato_numero(str(iva_ret_nc))
                        SubElement(detalle, "valorRetRenta").text = self.formato_numero(str(renta_ret_nc))

            #TODO: Retenciones en Ventas es necesario sumar los valores por IVA y RENTA de las retenciones emitidos por cada cliente
            #TODO: Se debe iterar por cada cliente que se ha emitido un documento en el periodo que se informa
            
            #TODO: Escenario, se anulan documentos de diferentes autorizaciones en un mes
            #Si existe algun tipo de documento anulado 
            if invoice_canceled or credit_note_canceled or liquidation_canceled:
                #FACTURAS ANULADAS
                if invoice_canceled:
                    anulados = SubElement(root,"anulados")
                    for inv in invoice_canceled:
                        numero_factura=inv.number.split('-')
                        detalle = SubElement(anulados,"detalleAnulados")
                        SubElement(detalle, "tipoComprobante").text = "18"
                        SubElement(detalle, "establecimiento").text = numero_factura[0]
                        SubElement(detalle, "puntoEmision").text = numero_factura[1]
                        SubElement(detalle, "secuencialInicio").text = numero_factura[2]
                        SubElement(detalle, "secuencialFin").text = numero_factura[2]
                        SubElement(detalle, "autorizacion").text = inv.authorization_sales.number
                
                #NOTAS DE CREDITO ANULADAS
                if credit_note_canceled:
                    anulados = SubElement(root,"anulados")
                    for inv in credit_note_canceled:
                        numero_factura=inv.number.split('-')
                        detalle = SubElement(anulados,"detalleAnulados")
                        SubElement(detalle, "tipoComprobante").text = "04"
                        SubElement(detalle, "establecimiento").text = numero_factura[0]
                        SubElement(detalle, "puntoEmision").text = numero_factura[1]
                        SubElement(detalle, "secuencialInicio").text = numero_factura[2]
                        SubElement(detalle, "secuencialFin").text = numero_factura[2]
                        SubElement(detalle, "autorizacion").text = inv.autorization_credit_note_id.number
                #LIQUIDACIONES DE COMPRAS ANULADAS
                if liquidation_canceled:
                    for inv in liquidation_canceled:
                        numero_factura=inv.number.split('-')
                        detalle = SubElement(anulados,"detalleAnulados")
                        SubElement(detalle, "tipoComprobante").text = "03"
                        SubElement(detalle, "establecimiento").text = numero_factura[0]
                        SubElement(detalle, "puntoEmision").text = numero_factura[1]
                        SubElement(detalle, "secuencialInicio").text = numero_factura[2]
                        SubElement(detalle, "secuencialFin").text = numero_factura[2]
                        SubElement(detalle, "autorizacion").text = inv.authorization_liquidation.number

        #TODO: NOTAS DE DEBITO, EN ESPERA DE MODULO DE NOTAS DE DEBITO
        
        
        #TODO: Exportaciones, en espera de modulo de Exportaciones
        
        
        self.indent(root)
        return tostring(root,encoding="ISO-8859-1")
    
    
    def act_export(self, cr, uid, ids, context={}):
        this = self.browse(cr, uid, ids)[0]
        root = self.generate_xml(cr,uid,ids)
        this.name = "AT"+self.mes_lista[0]+self.mes_lista[1]+".xml"
        #self._write_attachment(cr,uid,ids,root,context)
        out=base64.encodestring(root)
        return self.write(cr, uid, ids, {'data':out, 'name':this.name, 'state': 'get'}, context=context)

        
        
    _name = 'sri.ats'
    
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
    
sri_ats()