__version__ = '0.0.1'


STIX_REPORT_FAMILY_AND_TYPES = [{'iobject_type': 'STIX_Package',
                                 'iobject_type_family': 'stix.mitre.org'}]

ACTIVE_MANTIS_EXPORTERS = ['hashes','ips','fqdns']

DASHBOARD_CONTENTS = {
    'ips' : {
        'basis': 'SingletonObservable',
        'name' : 'IPs',
        'types' : ['IPv4','IPv6'],
        'show_type_column': True,
    },
    'hashes' : {
        'basis': 'SingletonObservable',
        'name' : 'Hashes',
        'types' : ['MD5','SHA1','SHA256'],
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
    }
}

