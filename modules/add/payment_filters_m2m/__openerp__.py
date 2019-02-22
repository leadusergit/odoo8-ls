# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    All Rights Reserved.
#    info skype: german_442 email: (german.ponce@outlook.com)
############################################################################


{
    'name': 'Filtrar Pagos por Facturas',
    'version': '1',
    "author" : "German Ponce Dominguez",
    "category" : "TyP",
    'description': """

            Este modulo añade un filtro para poder seleccionar los pagos de una Factura.
                - Añade un campo Many2Many donde puedes seleccionar las Facturas.
                - Boton Filtrar, que hace un barrido de los pagos a aplicar.
    """,
    "website" : "http://poncesoft.blogspot.com",
    "license" : "AGPL-3",
    "depends" : ["account"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    "account_view.xml",
                    ],
    "installable" : True,
    "active" : False,
}
