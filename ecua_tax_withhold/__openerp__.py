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
    "website" : "http://www.ecuadorenlinea.net/",
    "category" : "Ecuadorian Regulations",
    "depends" : [
                 'base',
                 'account',
                 'account_voucher',
                 'account_accountant',
                 'purchase',
                 'sale',
                 'stock',
                 'sale_stock',
                 'report_aeroo',
                 'report_aeroo_ooo',
                 'l10n_ec_niif_minimal',
                 'ecua_invoice',
                 #'ecua_documentos_sri',
                 ],
    "description": """
    SRI is the tax authority in Ecuador. SRI demands that to
    issue a document to retain a fee on purchases. It helps with 
    tax collection for tax authority.
    
    This module adds the base features for issuing tributary document
    called "withhold" in sales and purchases.
    
    This module is part of a bigger framework of "ecua" modules, 
    and reuses mainly code based on work by Christopher Ormaza and 
    improvements from TRESCLOUD and 4RSOFT.
    
    Config:
    In the company configuration the taxes 
    
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
