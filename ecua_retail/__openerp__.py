# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle
# Copyright (C) 2013  TRESCLOUD CÍA LTDA
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

{
    "name" : "Ecuador Retail Industry",
    "version" : "1.0",
   # 'sequence': 4,
    'complexity': "easy",
    "author" : "TRESCLOUD CÍA LTDA",
    "website" : "http://www.trescloud.com/",
    "category" : "Ecuadorian Regulations",
    # TODO agregar dependencia a aeroo
    "depends" : [
                 'base',
                 'sale',
                 'account',
                 'ecua_invoice',
                 'sale_order_for_retail',        
                 ],
    "description": """
    Adds retail features to sale order for ecuadorian localization
    Anade funcionalidades de venta al detalle a la localizacion ecuatoriana    
    
    Author,
    
    Andres Calle,
    TRESCLOUD Cía Ltda.
    """,
    "init_xml": [],
    "update_xml": [ 
                   'views/pos_view.xml',
                   ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
