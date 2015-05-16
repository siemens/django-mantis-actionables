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
from mantis_actionables.models import ActionableTag, ActionableTaggingHistory, Context, TagInfo, SingletonObservable

class Command(BaseCommand):
    """
    Delete dingos tags (and related actionables tags with respective context) that
    are passed as arguments.
    """


    def handle(self, *args, **options):

        tags_to_delete = args
        print "Attemt to delete %s" % args

        for tag_info in tags_to_delete:
            print "Treating %s" % tag_info
            affected_sos = SingletonObservable.objects.filter(actionable_tags_cache__contains=':%s' % tag_info)
            print "Found affected sos %s" % affected_sos
            for affected_so in affected_sos:
                at_cache = affected_so.actionable_tags_cache
                print "Existing cache  %s" % at_cache
                tags = at_cache.split(',')
                new_cache = []
                for tag in tags:
                    if not (':%s' % tag_info) in tag:
                        new_cache.append(tag)
                new_cache = ','.join(new_cache)
                print "New cache  %s" % new_cache
                affected_so.actionable_tags_cache=new_cache
                affected_so.save()

            TagInfo.objects.filter(name=tag_info).delete()
