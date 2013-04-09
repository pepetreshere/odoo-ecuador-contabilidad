# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Christopher Ormaza, Ecuadorenlinea.net
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Ecuador - Accounting Chart Minimal IFRS compliance',
    'version': '1.15',
    'category': 'Localization/Account Charts',
    'description': """
    This is the base module to manage the accounting chart for Ecuador minimal IFRS compliance.
    """,
    'author': 'Christopher Ormaza, Ecuadorenlinea.net',
    'depends': [
                'account',
                'base_vat',
                'base_iban',
                'account_chart',
                ],
    'init_xml': [],
    'update_xml': [
                'data/account_tax_code.xml',
                'data/account_chart.xml',
                'data/account_tax_104.xml',
                'data/account_tax_103.xml',
                'views/l10n_chart_ec_niif_minimal_wizard.xml',
                'views/account_tax_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
}
