#########################################################################
# Copyright (C) 2010  Christopher Ormaza, Ecuadorenlinea.net	        #
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
    "name" : "Verificador de Cédula/RUC Ecuador",
    "version" : "1.0",
    "author" : "Christopher Ormaza, Ecuadorenlinea.net",
    "website" : "http://www.openerpecuador.org/",
    "category" : "Ecuadorian Regulations",
    "depends" : ['base'],
    "description": """
    Provide a verification of Cedula and Ruc for Ecuador Legislation, only for information porpouse
    """,
    "init_xml": [],
    "update_xml": [
     'views/verificar_ruc_cedula_view.xml',
     'views/company_view.xml',
     'installer.xml'
    ],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
