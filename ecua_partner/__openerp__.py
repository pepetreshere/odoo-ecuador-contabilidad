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
    "name" : "Ecuador Partner Enhancements / Mejoras a los contactos para Ecuador",
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
                 'base_vat',
                 'crm',
                 ],
    "description": """
    This module improves partner view to include
    - Commercial por defecto igual al del usuario actual
    - Equipo de venta por defecto igual al del usuario actual
    - Pais por defecto igual al del usuario actual
    - Posicion fiscal por defecto igual a la primera de la lista
      (en configuracion normal corresponde a persona natural)
    - Validar RUC (VAT) con el modulo base_vat
    - Anade cliente CONSUMIDOR FINAL
    
    This module is part of a bigger framework of "ecua" modules developed by 
    TRESCLOUD.
    
    Author,
    
    Andres Calle,
    TRESCLOUD Cía Ltda.
    """,
    "init_xml": [],
    "update_xml": [ 
                   'views/res_partner_view.xml',
                   'views/res_company_view.xml',
                   ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
