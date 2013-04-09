# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008-2012 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields
from osv import osv
import netsvc
import tools
import os, base64

class report_aeroo_installer(osv.osv_memory):
    _name = 'report.aeroo.installer'
    _inherit = 'res.config.installer'

    def _get_image(self, cr, uid, context=None):
        path = os.path.join('report_aeroo','config_pixmaps','module_banner.png')
        image_file = file_data = tools.file_open(path,'rb')
        try:
            file_data = image_file.read()
            return base64.encodestring(file_data)
        finally:
            image_file.close()

    def _get_image_fn(self, cr, uid, ids, name, args, context=None):
        image = self._get_image(cr, uid, context)
        return dict.fromkeys(ids, image) # ok to use .fromkeys() as the image is same for all 

    _columns = {
        'link':fields.char('Original developer', size=128, readonly=True),
        'config_logo': fields.function(_get_image_fn, string='Image', type='binary', method=True),
        
    }

    _defaults = {
        'config_logo': _get_image,
        'link':'http://www.alistek.com',
    }

report_aeroo_installer()

