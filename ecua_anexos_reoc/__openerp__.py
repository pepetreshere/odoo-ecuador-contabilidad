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
{
        "name" : "Ecuadorian Anexos",
        "version" : "1.0",
        "author" :  "Christopher Ormaza, Ecuadorenlinea.net",
        "website" : "http://www.ecuadorenlinea.net/",
        "category" : "Ecuadorian Legislation",
        "description": """   """,
        "depends" : ['base',
                     'ecua_documentos_sri',
                     'account',
                     'l10n_ec_niif_minimal', 
                     'ecua_facturas_manual',
                     'ecua_liquidacion_compras', 
                     'ecua_notas_credito_manual',
                     'ecua_retenciones_manual'],
        "init_xml" : [ ],
        "demo_xml" : [ ],
        "update_xml" : [
                        'views/reoc_view.xml',
                        'security/ir.model.access.csv'
                         ],
        "installable": True
}