{
        "name" : "Ecuador payments",
        "version" : "1.0",
        "author" : "David Romero",
        "website" : "http://www.trescloud.com",
        "category" : "Vertical Modules/Parametrization",
        "description": """Payment """,
        "depends" : ["base","account_voucher",
                     #"ecua_invoice_type"
                     ],
        "init_xml" : [ ],
        #"data" : [ 'data/ir.model.access.csv',],
        "demo_xml" : [ ],
        "update_xml" : [
                        'views/account_voucher_view.xml',
                        'security/ir.model.access.csv',
                        ],
        "installable": True
     
}