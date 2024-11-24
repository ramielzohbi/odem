{
    'name': 'digri Event Management',
    'version': '1.0',
    'category': 'Events',
    'summary': 'Advanced Event Management System',
    'description': """
        Advanced Event Management System with:
        - Multi-language support
        - Category-based registration
        - Custom registration forms
        - Advanced access control
    """,
    'author': 'diggri llc',
    'website': 'https://diggri.com',
    'depends': [
        'base',
        'mail',
        'web',
        'website',
        'portal',
        'http_routing',
    ],
   'data': [
    'security/event_security.xml',
    'security/ir.model.access.csv',
    'data/event_sequence.xml',
    'views/event_views.xml',
    'views/category_views.xml',
    'views/registration_views.xml',
    'views/menus.xml',
    'templates/registration_form.xml',
    'templates/registration_success.xml',
    'templates/registration_status.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'event_management/static/src/css/registration_form.css',
            'event_management/static/src/js/registration_form.js',
        ],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'sequence': 1,
    'license': 'LGPL-3',
}