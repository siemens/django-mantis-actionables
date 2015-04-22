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

from django.core.exceptions import ObjectDoesNotExist

from mantis_actionables.core.crowdstrike import import_crowdstrike_csv


from mantis_actionables.models import  Context



class Command(BaseCommand):
    help = """
    Usage: context_name context_type
    where context_type in {%s}
    Forces context with name 'context_name' to be of given context type without any sanity checks
    (Use this to correct problems in context type caused by some bug).

    """ % ", ".join(Context.TYPE_RMAP.keys())


    def handle(self, *args, **options):


        try:
            context = Context.objects.get(name=args[0])
        except ObjectDoesNotExist:
            context = None

        if context:
            if args[1] in Context.TYPE_RMAP.keys():
                context.type= Context.TYPE_RMAP[args[1]]
                context.save()



