__version__ = '0.3.0'

import re

from dingos import DINGOS_MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX

MANTIS_ACTIONABLES_STIX_REPORT_FAMILY_AND_TYPES = [{'iobject_type': 'STIX_Package',
                                 'iobject_type_family': 'stix.mitre.org'}]

MANTIS_ACTIONABLES_ACTIVE_EXPORTERS = ['cybox_all']

DASHBOARD_CONTENTS = {
'email_addresses' : {
        'basis': 'SingletonObservable',
        'name': 'Email Addresses',
        'types' : ['Email_Address'],
        'show_type_column': True
    },

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
        'types' : ['FQDN'],
        'show_type_column': False
    },
    'urls' : {
        'basis': 'SingletonObservable',
        'name': 'URLs',
        'types' : ['URL'],
        'show_type_column': True
    },

}

MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX = DINGOS_MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX

MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH = ""

MANTIS_ACTIONABLES_SRC_META_DATA_FUNCTION_PATH = ""


