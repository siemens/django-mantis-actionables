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

from optparse import make_option
import os

from django.core.management.base import BaseCommand, CommandError

from mantis_actionables import tasks


class Command(BaseCommand):
    """
    This class implements the command for importing crowdstrike CSV indicator reports
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '-f',
            '--file',
            action='store',
            dest='csvfile',
            default=None,
            help='CSV File with Crowdstrike data to import'
        ),
    )

    def handle(self, *args, **options):
        if not options.get('csvfile'):
            raise CommandError('no file given')

        csv_file = options.get('csvfile')
        print 'importing file: %s' % csv_file

        if not os.path.isfile(csv_file):
            raise CommandError('"%s" cannot be accessed!' % csv_file)

        tasks.import_crowdstrike_csv(csv_file)
        tasks.import_crowdstrike_csv.apply_async((csv_file,))

        print 'file imported'