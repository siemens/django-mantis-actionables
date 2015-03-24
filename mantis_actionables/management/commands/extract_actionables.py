# Copyright (c) Siemens AG, 2015
#
# This file is part of MANTIS.  MANTIS is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or(at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import pytz
from datetime import datetime

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError

from ...mantis_import import process_STIX_Reports, import_singleton_observables_from_STIX_iobjects

class Command(BaseCommand):
    """
    This class implements the command for importing data from a mantis exporter
    """
    args = '<from_ts until_ts> using data time strings'
    help = 'create actionables out of the result of a mantis exporter, e.g. fqdn'

    option_list = BaseCommand.option_list + ( make_option('--timeframe',
                    nargs=2,
                    action='store',
                    dest='timeframe',
                    default=None,
                    help='Import timeframe: two date-times denoting from and to'),

                    make_option('--pk',
                    action='append',
                    dest='top_level_iobj_pks',
                    default=[],
                    help='List of pks of information objects representing Top-Level STIX reports from which'
                         ' actionables are to be extracted into mantis_actionables.'),
    )

    def handle(self, *args, **options):
        if len(args) != 0:
            raise CommandError("Wrong arguments.")
        if not options.get('top_level_iobj_pks') and not options.get('timeframe'):
            raise CommandError("Neither timeframe nor list of pks specified.")

        if options.get('top_level_iobj_pks') and options.get('timeframe'):
            raise CommandError("Specify either timeframe or list of pks")


        if options.get('timeframe'):
            try:
                from_time, to_time = options.get('timeframe')
                from_time = datetime.strptime(from_time,"%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('Etc/GMT+0'))
                to_time = datetime.strptime(to_time,"%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('Etc/GMT+0'))


            except ValueError:
                raise CommandError("wrong from_timestamp format, use Y-M-D H:M:S")


            process_STIX_Reports(from_time,to_time)

        elif options.get('top_level_iobj_pks'):
            top_level_iobj_pks = map(int,options.get('top_level_iobj_pks'))
            import_singleton_observables_from_STIX_iobjects(top_level_iobj_pks)


