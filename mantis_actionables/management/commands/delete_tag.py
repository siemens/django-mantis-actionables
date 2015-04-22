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

from mantis_actionables.core.crowdstrike import import_crowdstrike_csv

from dingos.models import TaggingHistory
from taggit.models import Tag
from mantis_actionables.models import ActionableTag, ActionableTaggingHistory, Context, TagName

class Command(BaseCommand):
    """
    Delete dingos tags (and related actionables tags with respective context) that
    are passed as arguments.
    """


    def handle(self, *args, **options):

        tags_to_delete = args

        for tag in tags_to_delete:
            #ActionableTaggingHistory.filter(tag__context__name=tag).delete()
            #TaggingHistory.filter(tag__name=tag).delete()

            Context.objects.filter(name=tag).delete()
            Tag.objects.filter(name=tag).delete()
            TagName.objects.filter(name=tag).delete()
