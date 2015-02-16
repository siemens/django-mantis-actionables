__version__ = '0.0.1'

import re

STIX_REPORT_FAMILY_AND_TYPES = [{'iobject_type': 'STIX_Package',
                                 'iobject_type_family': 'stix.mitre.org'}]

ACTIVE_MANTIS_EXPORTERS = ['cybox_all']

DASHBOARD_CONTENTS = {
    'ips' : {
        'basis': 'SingletonObservable',
        'name' : 'IPs',
        'types' : ['IP'],
        'show_type_column': True,
    },
    'hashes' : {
        'basis': 'SingletonObservable',
        'name' : 'Hashes',
        'types' : ['Hash'],
        'show_type_column': True,
    },
    'fqdns' : {
        'basis': 'SingletonObservable',
        'name': 'FQDNs',
        'types' : 'FQDN',
        'show_type_column': False
    },
    'urls' : {
        'basis': 'SingletonObservable',
        'name': 'URLs',
        'types' : 'URL',
        'show_type_column': False
    },
    'emails' : {
        'basis': 'SingletonObservable',
        'name': 'Email Addresses',
        'types' : ['Email_Address'],
        'show_type_column': False
    }

}

MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX = [
    re.compile(r"^INVES-[0-9]+(-[A-Za-z0-9]+)?$")
]

MANTIS_ACTIONABLES_STATUS_CREATION_FUNCTION_PATH = ""

MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH = ""



