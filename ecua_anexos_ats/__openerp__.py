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

{
        "name" : "Ecuadorian Anexos",
        "version" : "1.17",
        "author" :  "Christopher Ormaza Acosta, Ecuadorenlinea.net",
        "website" : "http://www.ecuadorenlinea.net/",
        "category" : "Ecuadorian Legislation",
        "description": """ATS for Commercial Companies""",
        "depends" : ['base',
                     'account',
                     'ecua_documentos_sri',
                     ],
        "init_xml" : [ 
                        'data/tipo_comprobantes.xml',
                        'data/sustento_tributario.xml',
                        'data/tipo_transaccion.xml',
                      ],
        "demo_xml" : [ ],
        "update_xml" : [
                        'security/ir.model.access.csv',
                        'data/codigo_regimen.xml',
                        'data/distrito_aduanero.xml',
                        'data/tarjeta_credito.xml',
                        'views/menu_ats.xml',
                        'views/codigo_regimen_view.xml',
                        'views/distrito_aduanero_view.xml',
                        'views/tipo_comprobante_view.xml',
                        'views/tipo_transaccion_view.xml',
                        'views/invoice_view.xml',
                        'views/company_view.xml',
                        'wizard/ats_view.xml',
                        #'test/test.yml',
                         ],
        "installable": True
}
