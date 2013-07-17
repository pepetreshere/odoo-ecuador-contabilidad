# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: Andres Calle, Andrea García
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
    "name" : "Ecuador Invoices / Facturas Ecuatorianas",
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
                 'stock',
                 'account',
                 ],
    "description": """
    In Ecuador additional rules applies to invoices:
    - it is needed to store the "current" name, address, VAT and phone.
    - it is needed to store the invoice number
    - voiding invoices allowed only to account managers
    
    This module is part of a bigger framework of "ecua" modules developed by 
    TRESCLOUD, EcuadorEnLinea y 4RSOFT.
    
    Author,
    
    Andres Calle,
    Andrea García
    TRESCLOUD Cía Ltda.
    """,
    "init_xml": [],
    "update_xml": [ 
                    'views/invoice_view.xml',
                    'views/shop_view.xml',
                    'views/res_users_view.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
