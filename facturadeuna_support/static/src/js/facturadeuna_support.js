openerp.facturadeuna_support = function(instance) {
    instance.web.client_actions.add('fdu.support.cursos.gratis', 'instance.facturadeuna_support.cursosgratis');
    instance.web.client_actions.add('fdu.support.pide.ayuda', 'instance.facturadeuna_support.pideayuda');
    instance.web.client_actions.add('fdu.support.manuales', 'instance.facturadeuna_support.manuales');
    instance.web.client_actions.add('fdu.support.changelog.ago2014', 'instance.facturadeuna_support.ago2014');
    instance.web.client_actions.add('fdu.support.changelog.dic2014', 'instance.facturadeuna_support.dic2014');
    instance.web.client_actions.add('fdu.support.main', 'instance.facturadeuna_support.main');
    var popup = function(url) {
        return window.open(url);
    };
    instance.facturadeuna_support.cursosgratis = function(parent, action) {
        return popup('http://www.trescloud.com/openerp-ecuador-eventos');
    };
    instance.facturadeuna_support.pideayuda = function(parent, action) {
        return popup('https://trescloud.zendesk.com/hc/es/requests/new')
    };
    instance.facturadeuna_support.manuales = function(parent, action) {
        return popup('https://trescloud.zendesk.com/hc/es');
    };
    instance.facturadeuna_support.ago2014 = function(parent, action) {
        return popup('http://us5.campaign-archive2.com/?u=9318e3a3cc4a8d03012f20683&amp;id=e25f8f6b69&amp;e=[UNIQID')
    };
    instance.facturadeuna_support.dic2014 = function(parent, action) {
        //TODO ponerle un documento acorde a la version de Diciembre
        return popup('http://us5.campaign-archive2.com/?u=9318e3a3cc4a8d03012f20683&amp;id=e25f8f6b69&amp;e=[UNIQID')
    };
    instance.facturadeuna_support.main = instance.web.Widget.extend({
        template:'fdu.support.main',
        events: {
            'click #cursosgratis': 'go_cursosgratis',
            'click #pideayuda': 'go_pideayuda',
            'click #manuales': 'go_manuales',
            'click #ago2014': 'go_ago2014',
            'click #dic2014': 'go_dic2014'
        },
        go_cursosgratis: function() { instance.facturadeuna_support.cursosgratis(null, null); },
        go_pideayuda: function() { instance.facturadeuna_support.pideayuda(null, null); },
        go_manuales: function() { instance.facturadeuna_support.manuales(null, null); },
        go_ago2014: function() { instance.facturadeuna_support.ago2014(null, null); },
        go_dic2014: function() { instance.facturadeuna_support.dic2014(null, null); }
    });
};