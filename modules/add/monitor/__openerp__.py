{
    "name" : "Monitor",
    "version" : "1.0",
    "author" : "JMC",
    "category": 'Configuracion',
    "description": """
                    Modulos control de instancias
                   """,
    'website': 'http://www.leadsolutions.ec/',
    'init_xml': [],
    "depends": ['sale', 'account'],
    'data': [
        #'security/groups.xml',
        #'security/ir.model.access.csv',
        'views/menuitems.xml',
        'views/sequence.xml',
        'workflows/wkf_liquidation.xml',
        'views/views_base.xml',
        'views/views_liquidation.xml',
        'views/views_extended.xml',
        'views/views_history.xml',
        'report/m_dashboard_liquidation.xml',
        'report/report_liquidation_details.xml',
        'emails/email_request.xml',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
