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
__author__ = 'Philipp Lang'

from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from ...mantis_import import process_STIX_Reports

class Command(BaseCommand):
    """
    This class implements the command for importing data from a mantis exporter
    """
    args = '<from_ts until_ts> using data time strings'
    help = 'create actionables out of the result of a mantis exporter, e.g. fqdn'

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("no from_timestamp specified")
        if len(args) > 2:
            raise CommandError("too much args specified")

        try:
            imported_since = datetime.strptime(args[0],"%Y-%m-%d")
        except ValueError:
            raise CommandError("wrong from_timestamp format: Y-M-D")
        imported_until = None

        if len(args) == 2:
            try:
                imported_until = datetime.strptime(args[1],"%Y-%m-%d")
            except ValueError:
                raise CommandError("wrong until_timestamp format: Y-M-D")

        process_STIX_Reports(imported_since,imported_until)


