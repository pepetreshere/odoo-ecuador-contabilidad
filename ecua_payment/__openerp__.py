{
        "name" : "trescloud_ecua_payment",
        "version" : "1.0",
        "author" : "David Romero",
        "website" : "http://www.trescloud.com",
        "category" : "Vertical Modules/Parametrization",
        "description": """Payment """,
        "depends" : ["base"],
        "init_xml" : [ ],
        #"data" : [ 'data/ir.model.access.csv',],
        "demo_xml" : [ ],
        "update_xml" : ['security/account_security.xml',
                        'security/ir.model.access.csv',
                        ],
        "installable": True
     
}