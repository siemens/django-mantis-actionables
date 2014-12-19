
Todos
=====

Write an importer
-----------------

- In ``mantis_actionables/mantis_import.py``, write code
  for the provided function stubs:

  - extract_singleton_observable
  - process_STIX_Reports

Write a command-line command 'extract_actionables' for executing the import
---------------------------------------------------------------------------

Look at Django documentation on how to add command-line commands
(they must be placed in subfolder 'management/commands' ...
The command should accept 'from' 'until' as command line arguments
accepting date-time strings.


Write a generic results view
----------------------------

Taking code/inspiration from django-mantis-dashboard,
use the js-data-tables framework to display the contents
of mantis-actionables:

- read from __init__.py the configuration of
  DASHBOARD_CONTENTS. Currently this is:

    DASHBOARD_CONTENTS = [{'basis': 'SingletonObservable',
                       'name' : 'IPs',
                       'types' : ['IPv4','IPv6'],
                       'show_type_column': True,
                       },
                      {'basis': 'SingletonObservable',
                       'name' : 'Hashes',
                       'types' : ['MD5','SHA1','SHA256'],
                       'show_type_column': True,
                       },
                      {'basis': 'SingletonObservable',
                       'name': 'FQDNs',
                       'types' : 'FQDN',
                       'show_type_column': False},
                      {'basis': 'SingletonObservable',
                       'name': 'URLs',
                       'types' : 'URL',
                       'show_type_column': False}]

- for each item, create a data table that
  displays the data for the chosen SingletonObservableTypes
  and shows the following columns:

  - Source Timestamp (data ordered by this)
  - SingletonObservableType (if 'show_type_column' set to True)
  - Value
  - TLP
  - Namespace and Name of STIX Report object from which
    this source originated




  
