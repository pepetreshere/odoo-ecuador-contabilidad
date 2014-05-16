{
        "name" : "trescloud_group_tax",
        "version" : "1.0",
        "author" : "OpenERP SA",
        "website" : "http://www.openerp.com",
        "category" : "Vertical Modules/Parametrization",
        "description": """Access Account Tax""",
        "depends" : ["base","hr_timesheet_invoice","hr_contract","account_followup","account_voucher","crm_default_sales_team","base_calendar","hr_payroll","ecua_tax_withhold","ecua_sri_refund","product","account_analytic_default","hr_advance_payment","account_payment","hr","hr_attendance","hr_timesheet","ecua_hr","ecua_autorizaciones_sri","base","account_budget","ecua_invoice_type","hr_expense","account","account_analytic_analysis","resource","account_asset","account_check_writing","hr_holidays","hr_extra_input_output"],
        "init_xml" : [ ],
        "data" : [ 'data/ir.model.access.csv',],
        "demo_xml" : [ ],
        "update_xml" : ['security/account_security.xml',
                        'security/ir.model.access.csv',
                        ],
        "installable": True
     
} 