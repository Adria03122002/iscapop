# -*- coding: utf-8 -*-
{
    'name': "iscapop",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',           # Seguridad (accesos)
        'views/iscapop_categories_views.xml',      # Vistas de categorías
        'views/iscapop_stock_status_wizard.xml',          # wizard para cambiar el X stock de estado
        'views/iscapop_send_stock_wizard_views.xml',      # Wizards para enviar stock a otra clase
        'views/iscapop_locations_views.xml',       # Vistas de ubicaciones
        'views/iscapop_report_disposal_template.xml', #Generar el pdf para la baja de materiales
        'views/iscapop_report_donation.xml',
        'views/iscapop_items_views.xml',           # Vistas de items (que se utilizan en el menú)
        'views/iscapop_donations.xml',            # Vista para las donaciones
        'views/iscapop_menu.xml',                  # Menús (dependen de las vistas y acciones)
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}

