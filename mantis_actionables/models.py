# -*- coding: utf-8 -*-

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

from django.db import models
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


from dingos.models import InfoObject, Fact, FactValue, Identifier

class Action(models.Model):
    timestamp = models.DateTimeField()

    user = models.ForeignKey(User,
                             # We allow this to be null to mark
                             # actions carried out by the system
                             null=True)

    comment = models.TextField(blank=True)


    # Actions can be linked to different models:
    # - primitive Observables
    # - IDS Signatures

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    affected = generic.GenericForeignKey('content_type', 'object_id')

class Source(models.Model):
    timestamp = models.DateTimeField()

    # If the source is MANTIS, we populate the following fields:

    iobject = models.ForeignKey(InfoObject,
                                null=True,
                                related_name='actionable_thru')
    iobject_fact = models.ForeignKey(Fact,related_name='actionable_thru')
    iobject_factvalue = models.ForeignKey(FactValue,
                                          null=True,
                                          related_name='actionable_thru')
    top_level_iobjects = models.ManyToManyField(InfoObject,related_name='related_actionable_thru')

    # If the source is a manual import, we reference the Import Info

    import_info = models.ForeignKey("ImportInfo",
                                    null=True,
                                    related_name = 'actionable_thru')

    # Sources can be linked to different models:
    # - primitive Observables
    # - IDS Signatures

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    yielded = generic.GenericForeignKey('content_type', 'object_id')


class PrimitiveObservableType(models.Model):
    name = models.CharField(max_length=255)

class Status(models.Model):

    # Status can be linked to different models:
    # - primitive Observables
    # - IDS Signatures

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    yielded = generic.GenericForeignKey('content_type', 'object_id')

class PrimitiveObservable(models.Model):
    type = models.ForeignKey(PrimitiveObservableType)
    value = models.CharField(max_length=2048)

    # We keep track of
    # - actions performed (usually status changes)
    # - sources (import or repeated finding)

    actions = generic.GenericRelation(Action,related_query_name='primitive_observables')
    source = generic.GenericRelation(Source,related_query_name='primitive_observables')

    class Meta:
        unique_together = ('type', 'value')


class SignatureType(models.Model):
    name = models.CharField(max_length=255)

class IDSSignature(models.Model):
    type = models.ForeignKey(SignatureType)
    content = models.TextField()

    actions = generic.GenericRelation(Action,related_query_name='ids_signatures')
    source = generic.GenericRelation(Source,related_query_name='ids_signatures')


class ImportInfo(models.Model):
    user = models.ForeignKey(User,
                             # We allow this to be null to mark
                             # imports carried out by the system
                             null=True)

    iobject_identifier = models.ForeignKey(Identifier,
                                           null=True,
                                           help_text="If provided, should point to the identifier"
                                                     " of a STIX Incident object")

    comment = models.TextField(blank=True)


