#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2010-2011 STRACONX S.A. (<http://openerp.straconx.com>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields


class region(osv.osv):
    _name = 'res.region'
    _description = 'region'
    _columns = {
        'name': fields.char('region Name', size=64,
            help='The full name of the region.', required=True, translate=True),
        'code': fields.char('region Code', size=2,
            help='The Region code in two chars.\n'
            'You can use this field for quick search.', required=True),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'The name of the region must be unique !'),
        ('code_uniq', 'unique (code)',
            'The code of the region must be unique !')
    ]

    def name_search(self, cr, user, name='', args=None, operator='ilike',
            context=None, limit=100):
        if not args:
            args=[]
        if not context:
            context={}
        ids = False
        if len(name) == 2:
            ids = self.search(cr, user, [('code', 'ilike', name)] + args,
                    limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args,
                    limit=limit, context=context)
        return self.name_get(cr, user, ids, context)
    _order='name'

    #def create(self, cursor, user, vals, context=None):
        #if 'code' in vals:
            #vals['code'] = vals['code'].upper()
        #return super(region, self).create(cursor, user, vals,
                #context=context)

    #def write(self, cursor, user, ids, vals, context=None):
        #if 'code' in vals:
            #vals['code'] = vals['code'].upper()
        #return super(region, self).write(cursor, user, ids, vals,
                #context=context)

region()

class regionZone(osv.osv):
    _description='res.region.state'
    _name = 'res.region.state'
    _columns = {
        'region_id': fields.many2one('res.region', 'region',required=True),
        'name': fields.char('Zone Name', size=64,required=True),
        'code': fields.char('Zone Code', size=10,help='The zone code in max ten chars.\n', required=True),
    }
    def name_search(self, cr, user, name='', args=None, operator='ilike',
            context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        ids = self.search(cr, user, [('code', 'ilike', name)] + args, limit=limit,
                context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args,
                    limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'The name of the zone must be unique !'),
        ('code_uniq', 'unique (code)',
            'The code of the zone must be unique !')
    ]

    _order = 'name'

regionZone()


class CountryState(osv.osv):
    _inherit = 'res.country.state'
    _columns = {
        'city_ids': fields.one2many('city.city', 'state_id', 'Cities'),
        'region_id': fields.many2one('res.region', 'Region'),
    }
CountryState()

class city(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for line in self.browse(cr, uid, ids):
            state = line.state_id.name
            region = line.state_id.region_id.name       
            country = line.state_id.country_id.name
            #parish = line.sector_id.parish
            #if parish is None:
                #loc = "%s, %s, %s, %s" %(line.name, state, region, country)
            #else:
                #loc = "%s, %s, %s, %s, %s" %(parish, line.name, state, region, country)
            #sector = line.sector_id.sector
            #if sector is None:
                #loc = "%s, %s, %s, %s" %(line.name, state, region, country)
            #else: 
            loc = "%s, %s, %s, %s" %(line.name, state, region, country)
            location = loc.upper()
            res.append((line['id'], location))
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        res = super(city, self).search(cr, uid, args, offset, limit, order, context, count)
        if not res and args:
            args = [('zipcode', 'ilike', args[0][2])]
            res = super(city, self).search(cr, uid, args, offset, limit, order, context, count)
        return res
        
    _name = 'city.city'
    _description = 'City'
    _columns = {
        'state_id': fields.many2one('res.country.state', 'State', required=True, select=1),
        'region_id': fields.many2one('res.region.state', 'Region', select=1),
        'name': fields.char('City', size=64, required=True, select=1),
        'sector_id': fields.one2many('res.partner.parish','name', 'Sector and Parish'),
        'zipcode': fields.char('ZIP', size=64, required=True, select=1),
        'parroquia_ids':fields.one2many('res.parroquia', 'city_id', 'Parroquias', required=False), 
        
    }
city()

class res_partner_sector(osv.osv):
    _name = 'res.partner.sector'
    _description = 'Parish and Sectors'
    _columns = {
        'parish': fields.char('Parish Name', size=64, help='The full name of Parish'),
        'sector': fields.char('Sector Name', size=64, help='The full name of Sector'),
        'name': fields.many2one('city.city', 'Location'),
    }
    _sql_constraints = [('name_location_uniq', 'unique (name,sector,parish)','The name of the sector, parish and city must be unique !')]

    _order='location'

res_partner_sector()

class res_partner_address(osv.osv): 
    _inherit = "res.partner.address"
#    def _get_parroquia(self, cr, uid, ids, field_name, arg, context):
#        res={}
#        for obj in self.browse(cr,uid,ids):
#            if obj.location:
#                res[obj.id] = obj.location.parroquia_ids[0].id
#            else:
#                res[obj.id] = ""
#        return res
#
#    def _parroquia_id_search(self, cr, uid, obj, name, args, context):
#        if not len(args):
#            return []
#        new_args = []
#        for argument in args:
#            operator = argument[1]
#            value = argument[2]
#            ids = self.pool.get('res.parroquia').search(cr, uid, [('name',operator,value)], context=context)
#            new_args.append( ('location','in',ids) )
#        if new_args:
#            # We need to ensure that locatio is NOT NULL. Otherwise all addresses
#            # that have no location will 'match' current search pattern.
#            new_args.append( ('location','!=',False) )
#        return new_args

    def _get_zip(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,uid,ids):
            if obj.location:
                res[obj.id] = obj.location.zipcode
            else:
                res[obj.id] = ""
        return res

    def _zip_search(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid, [('zipcode',operator,value)], context=context)
            new_args.append( ('location','in',ids) )
        if new_args:
            # We need to ensure that locatio is NOT NULL. Otherwise all addresses
            # that have no location will 'match' current search pattern.
            new_args.append( ('location','!=',False) )
        return new_args

    def _get_city(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,uid,ids):
            if obj.location:
                res[obj.id] = obj.location.name
            else:
                res[obj.id] = ""
        return res

    def _city_search(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid, [('name',operator,value)], context=context)
            new_args.append( ('location','in',ids) )
        if new_args:
            # We need to ensure that locatio is NOT NULL. Otherwise all addresses
            # that have no location will 'match' current search pattern.
            new_args.append( ('location','!=',False) )
        return new_args
        
    def _get_region(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,uid,ids):
            if obj.location:
                res[obj.id] = [obj.location.region_id.id, obj.location.region_id.name]
            else:
                res[obj.id] = False
        return res

    def _region_id_search(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid, [('region_id',operator,value)], context=context)
            new_args.append( ('location','in',ids) )
        if new_args:
            # We need to ensure that locatio is NOT NULL. Otherwise all addresses
            # that have no location will 'match' current search pattern.
            new_args.append( ('location','!=',False) )
        return new_args

    def _get_state(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,uid,ids):
            if obj.location:
                res[obj.id] = [obj.location.state_id.id, obj.location.state_id.name]
            else:
                res[obj.id] = False
        return res

    def _state_id_search(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid, [('state_id',operator,value)], context=context)
            new_args.append( ('location','in',ids) )
        if new_args:
            # We need to ensure that locatio is NOT NULL. Otherwise all addresses
            # that have no location will 'match' current search pattern.
            new_args.append( ('location','!=',False) )
        return new_args

    def _get_country(self, cr, uid, ids, field_name, arg, context):
        res={}
        for obj in self.browse(cr,uid,ids):
            if obj.location:
                res[obj.id] = [obj.location.state_id.country_id.id, obj.location.state_id.country_id.name]
            else:
                res[obj.id] = False
        return res

    def _country_id_search(self, cr, uid, obj, name, args, context):
        if not len(args):
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('res.country.state').search(cr, uid, [('country_id',operator,value)], context=context)
            address_ids = []
            for country in self.pool.get('res.country.state').browse(cr, uid, ids, context):
                ids += [city.id for city in country.city_ids]
            new_args.append( ('location','in',tuple(ids)) )
        if new_args:
            # We need to ensure that location is NOT NULL. Otherwise all addresses
            # that have no location will 'match' current search pattern.
            new_args.append( ('location','!=',False) )
        return new_args

    _columns = {
        'location': fields.many2one('city.city', 'Location'),
        'phone2':fields.char('Phone 2',size=13),
        'sector': fields.char('Sector',size=150),
        'parish': fields.char('Parish',size=150),
        'zip': fields.function(_get_zip, fnct_search=_zip_search, method=True, type="char", string='Zip', size=24),
        'city': fields.function(_get_city, fnct_search=_city_search, method=True, type="char", string='City', size=128, store=True),
        'region_id': fields.function(_get_region, fnct_search=_region_id_search, obj="res.region.state", method=True, type="many2one", string='Region', store=True), 
        'state_id': fields.function(_get_state, fnct_search=_state_id_search, obj="res.country.state", method=True, type="many2one", string='State', store=True), 
        'country_id': fields.function(_get_country, fnct_search=_country_id_search, obj="res.country" ,method=True, type="many2one", string='Country', store=True),
        'parroquia_id':fields.many2one('res.parroquia', 'Parroquia', required=False),  
    }
    
    def onchange_location(self, cr, uid, ids, location, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if location:
            loc = self.pool.get('city.city').browse(cr, uid, location)
            value.update({
                          'zip': loc.zipcode or None,
                          'city': loc.name or None,
                          'country_id': loc.state_id and loc.state_id.country_id and loc.state_id.country_id.id or None,
                          'state_id': loc.state_id and loc.state_id.id or None,
                          'parroquia_id': None,
                          })
        else:
            value.update({
                          'zip': None,
                          'city': None,
                          'country_id': None,
                          'state_id': None,
                          'parroquia_id': None,
                          })
        return {'value': value, 'domain': domain }
res_partner_address()


class res_parroquia(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'res.parroquia'
    _description = 'Parroquias'

    _columns = {
            'name':fields.char('Nombre', size=255, required=True, readonly=False),
            'city_id':fields.many2one('city.city', 'Ciudad', required=True), 
            'type':fields.selection([
                ('urbana','Urbana'),
                ('rural','Rural'),
                 ],    'Tipo', select=True, readonly=False,required=True),
            
        }
    _defaults = {  
        'type': 'urbana',  
        }
res_parroquia()




