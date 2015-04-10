{
        "name" : "Ecuador payments",
        "version" : "1.0",
        "author" : "TRESCLOUD CÍA LTDA",
        "website" : "http://www.trescloud.com",
        "category" : "Ecuadorian Regulations",
        "description": """ 
        Enhances the payments according to Ecuadorian commercial practice inluding:
        -Alertar cuando una linea de pago excede el saldo total, bloqueando pagos en exceso.
        -Mejoras en las traducciones
        -Boton 2en1 "Imprimir y Pagar"
        -Facilidades para conciliar saldo de pago a otras cuentas mediante el visto bueno "Forzar Saldo de la Diferencia"
        -Mejoras a los grupos de seguridad
        
        Autores
        
        David Romero, Andres Calle
        """,
        "depends" : ["base","account_voucher",
                     ],
        "init_xml" : [ ],
        #"data" : [ 'data/ir.model.access.csv',],
        "demo_xml" : [ ],
        "update_xml" : [
                        'views/account_voucher_view.xml',
                        'views/account_journal_view.xml',
                        'views/replenishment_controlled_view.xml',
                        'security/ir.model.access.csv',
                        'data/sequence.xml',
                        ],
        "installable": True
     
}