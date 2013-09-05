# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, Patricio Rangles
# Copyright (C) 2013  TRESCLOUD Cia Ltda
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
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
import time

class res_partner(osv.osv):
    _inherit = "res.partner"
    _name = "res.partner"
    
    # agregamos codigo de ecuador al modulo base_vat
    #_ref_vat['ec']='EC1234567891001'
    _ref_vat = {
                'ec': 'EC1234567891001',
                }
        
    def _get_user_default_sales_team(self, cr, uid, ids, context={}):
        user= self.pool.get('res.users').browse(cr,uid,uid)
        sale_team_id=user.default_section_id.id
        return sale_team_id or False

    def _get_user_country_id(self, cr, uid, ids, context={}):
        #TODO - Validar si sirve para entorno multicompania
        company_id = self.pool.get('res.users').browse(cr,uid,uid).company_id
        country_id = company_id.country_id.id
        if country_id:
            return country_id
        return    
 
    _columns = {
                'comercial_name': fields.char('Comercial Name', size=256),
#                'shop_id':fields.many2one('sale.shop', 'Shop', readonly=True, states={'draft':[('readonly',False)]}),
#                'invoice_address':fields.char("Invoice address", help="Invoice address as in VAT document, saved in invoice only not in partner"),
#                'invoice_phone':fields.char("Invoice phone", help="Invoice phone as in VAT document, saved in invoice only not in partner"),
               }

    _defaults = {
                 'user_id': lambda self, cr, uid, context: uid,
                 'comercial_name': "",
                 'section_id': _get_user_default_sales_team,
                 'country_id': _get_user_country_id,
                 'date': fields.date.context_today
                 # TODO - Evaluar los modulos account_fiscal_position_rule, account_fiscal_position_country, y account_fiscal_position_country_sale
                 #'property_account_position': _get_default_fiscal_position_id,
                 }
    #    _sql_constraints = [
    #    ]
    #    _order = 'name asc'


    # Ecuador VAT validation, contributed by TRESCLOUD (info@trescloud.com)
    # and based on https://launchpad.net/openerp-ecuador
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_ruc_spri(self,ruc):
        try:
            #validate VAT has 10 or 13 digits
            if (int(ruc[0]+ruc[1]))<23:
                 prueba1=True
            else:
                 prueba1=False
            
            if (int(ruc[2])==9):
                 prueba2=True
            else:
                 prueba2=False    
        
            #split VAT and take first 9 digits
            val0=int(ruc[0])*4
            val1=int(ruc[1])*3
            val2=int(ruc[2])*2
            val3=int(ruc[3])*7
            val4=int(ruc[4])*6
            val5=int(ruc[5])*5
            val6=int(ruc[6])*4
            val7=int(ruc[7])*3
            val8=int(ruc[8])*2
         
            tot=val0+val1+val2+val3+val4+val5+val6+val7+val8
            veri=tot-((tot/11))*11
         
            if(veri==0):
                if((int(ruc[9]))== 0):
                    prueba3=True
                else:
                    prueba3=False
            else:
                if((int(ruc[9]))==(11-veri)):
                    prueba3=True
                else:
                    prueba3=False
        
            if((int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                return True
            else: 
                return False
        except:
            return False
        
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec  
    #SECTOR PUBLICO
    def verifica_ruc_spub(self,ruc):
        try: 
            if (int(ruc[0]+ruc[1]))<23:
                prueba1=True
            else:
                prueba1=False
            
            if (int(ruc[2])==6):
                prueba2=True
            else:
                prueba2=False    
        
            val0=int(ruc[0])*3
            val1=int(ruc[1])*2
            val2=int(ruc[2])*7
            val3=int(ruc[3])*6
            val4=int(ruc[4])*5
            val5=int(ruc[5])*4
            val6=int(ruc[6])*3
            val7=int(ruc[7])*2
         
            tot=val0+val1+val2+val3+val4+val5+val6+val7
            veri=tot-((tot/11))*11
         
            if(veri==0):
                if((int(ruc[8]))== 0):
                    prueba3=True
                else:
                    prueba3=False
            else:
                if((int(ruc[8]))==(11-veri)):
                    prueba3=True
                else:
                    prueba3=False
        
            if((int(ruc[9]))+(int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                 return True
            else: 
                return False
        except:
            return False

    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_ruc_pnat(self,ruc):
        try:
            if (int(ruc[0]+ruc[1]))<23:
                prueba1=True
            else:
                prueba1=False
            
            if (int(ruc[2])<6):
                prueba2=True
            else:
                prueba2=False    
        
            valores = [ int(ruc[x]) * (2 - x % 2) for x in range(9) ]
            suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
            veri = 10 - (suma - (10*(suma/10)))
            if int(ruc[9]) == int(str(veri)[-1:]):
                prueba3= True
            else:
                prueba3= False
                
            if((int(ruc[10]))+(int(ruc[11]))+(int(ruc[12]))>0):
                prueba4=True
            else:
                prueba4=False
        
            if(prueba1 and prueba2 and prueba3 and prueba4):
                return True
            else: 
                return False
        except:
            return False
        
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_cedula(self,ced):
        try:
            if ced!='9999999999':
                valores = [ int(ced[x]) * (2 - x % 2) for x in range(9) ]
                suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
                veri = 10 - (suma - (10*(suma/10)))
                if int(ced[9]) == int(str(veri)[-1:]):
                    return True
                else:
                    return False
            else:
                return False
        except:
            return False
        
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    def verifica_id_cons_final(self,id):
        b=True
        try:
            for n in id:
                if int(n) != 9:
                    b=False
            return b
        except:
            return False
   
    # TRESCLOUD TODO - Incluir estas funciones en el espacio de nombres de check_vat_ec
    # TRESCLOUD TODO - Revisar la necesidad de esta funcion
    #    def _defined_type_ref(self, cr, uid, ids, field_name, arg, context=None):
    #        res={}
    #        for partner in self.browse(cr, uid, ids, context):
    #            ref = partner['ref']
    #            if(len(ref)==13):
    #                if self.verifica_ruc_pnat(ref) or self.verifica_ruc_spri(ref) or self.verifica_ruc_spub(ref):
    #                    res[partner.id]= 'ruc'
    #                elif self.verifica_id_cons_final(ref):
    #                    res[partner.id]= 'consumidor'
    #            elif (len(ref)==10):
    #                if self.verifica_cedula(ref):
    #                    res[partner.id]= 'cedula'
    #        return res

    # Ecuador VAT validation, contributed by TRESCLOUD (info@trescloud.com)
    # and based on https://launchpad.net/openerp-ecuador
    def check_vat_ec(self, vat):
        #Separa companias de personas naturales
        # P.R. This version Don't return a dictionary, must return True or False
        
        #type_identification = ''
        valid = False
        
        #validamos que solo se utilicen caracteres numericos
        for i in vat:
            try:
                int(i)
            except:
                #return {
                #'type_ref' : type_identification,
                #'valid': valid
                #}
                return valid
        
        if(len(vat)==13):
            #Se verifica que el cliente es una compañia privada
            if(int(vat[2])==9):
                if self.verifica_ruc_spri(vat):
                    valid = True
                    #type_identification='ruc'
                elif self.verifica_id_cons_final(vat):
                    valid = True
                    #type_identification='consumidor'
            #Se verifica que sea una empresa estatal
            elif(int(vat[2])==6) and self.verifica_ruc_spub(vat):
                valid = True
                #type_identification='ruc'
            #Se verifica que el ruc sea de una persona natural
            elif(int(vat[2])<6) and self.verifica_ruc_pnat(vat):
                valid = True
                #type_identification='ruc'
        #Se verifica el número de cedula
        elif(len(vat)==10) and self.verifica_cedula(vat):
            valid = True
            #type_identification='cedula'
        #return {
               # 'type_ref' : type_identification,
               # 'valid': valid
               # }
        return valid
    
    def get_number_identification(self, vat):
        '''Función que toma como argumento el campo vat, se hace un slicing para tomar la parte númerica.'''  
       
        identification=''        
        if vat:
            identification = vat[2:]
        
        return identification
    
    def get_code_country(self, vat):
        '''Función que toma como argumento el campo vat, se hace un slicing para tomar la parte del código de país.'''
        
        code_country=''
        if vat:
            code_country = vat[:2] 
       
        return code_country
        
res_partner()
