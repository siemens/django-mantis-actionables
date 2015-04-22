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

from dingos.models import TaggingHistory
from taggit.models import Tag
from mantis_actionables.models import ActionableTag, ActionableTaggingHistory, Context, TagName



class Command(BaseCommand):
    """
    Rename a dingos tag (and context in actionables). Attention: this only
    works if the target tag does not exist yet!


    """


    def handle(self, *args, **options):

        tag_to_rename = args[0]
        rename_target = args[1]

        existing_dingos_tags = Tag.objects.filter(name=rename_target)
        existing_actionables_context = Context.objects.filter(name=rename_target)

        if existing_dingos_tags:
            raise CommandError("Dingos tag %s already exists" % rename_target)
        if existing_actionables_context:
            raise CommandError("Actionables context %s already exists" % rename_target)

        # Rename dingos tag
        try:
            tag = Tag.objects.get(name=tag_to_rename)
        except ObjectDoesNotExist:
            tag = None

        if tag:
            tag.name = rename_target
            tag.save()

        # Rename dingos tag
        try:
            context = Context.objects.get(name=tag_to_rename)
        except ObjectDoesNotExist:
            context = None

        if context:
            context.name = rename_target
            context.save()

            TagName.objects.filter(name=tag_to_rename).update(name=rename_target)



