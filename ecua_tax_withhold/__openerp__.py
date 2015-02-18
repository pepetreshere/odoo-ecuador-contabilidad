# -*- encoding: utf-8 -*-
########################################################################
#
# @authors: TRESCLOUD CÍA LTDA, 4RSOFT, Christopher Ormaza
# Copyright (C) 2013  Ecuadorenlinea.net
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
    "name" : "Ecuador Withhold Tax Document",
    "version" : "1.0",
   # 'sequence': 4,
    'complexity': "hard",
    "author" : "TRESCLOUD CÍA LTDA",
    "website" : "http://www.trescloud.com/",
    "category" : "Ecuadorian Regulations",
    "depends" : [
                 'base',
                 #'account', #ya es dependencia de ecua_invoice a travez del modulo l10n
                 #'account_voucher', #ya es dependencia de ecua_invoice a travez del account
                 #'account_accountant', #ya es dependencia de ecua_invoice a travez del account
                 #'purchase', #no es requerido para efectos estrictamente contables
                 #'sale', #no es requerido para efectos estrictamente contables, cuando se requiere se usa el modulo ecua_salte_to_invoice
                 #'stock', #no es requerido para efectos estrictamente contables vinculados a las retenciones
                 #'sale_stock', #no es requerido para efectos estrictamente contables vinculados a las retenciones
                 'report_aeroo',
                 'report_aeroo_ooo',
                 #'l10n_ec_niif_minimal', #ya es dependencia de ecua_invoice a travez del account
                 'ecua_invoice',
                 'ecua_payment', #requerido porq ecua_paymente agrega el concepto de cuenta de desajuste por defecto
                 'mail',
                 #'ecua_documentos_sri',
                 ],
    "description": """
    SRI is the tax authority in Ecuador. SRI demands that to
    issue a document to retain a fee on purchases. It helps with 
    tax collection for tax authority.
    
    This module adds the base features for issuing tributary document
    called "withhold" in sales and purchases, allowing for several features like:
    - Withhold for payed customer invoices
    - Withhold for open customer and supplier invoices
    - Other related features
    
    This module is part of a bigger framework of "ecua" modules 
    by TRESCLOUD.
    
    Config:
    In the company configuration the taxes
    In the journal the accounts linked to withhold journals 
    
    Authors,
    
    Andres Calle,
    Andrea García,
    Patricio Rangles,
    TRESCLOUD Cía Ltda.
    """,
    "init_xml": [],
    "update_xml": [ 
                    
                    'security/ir.model.access.csv',
                    'report/withhold_report.xml',
                    'workflow/withhold_workflow.xml',
                    'wizard/withhold_wizard_view.xml',
                    'views/company_view.xml',
                    'views/withhold_view.xml',
                    'views/withhold_config_view.xml',
                    'views/invoice_view.xml',
                    'data/sequence_data.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
