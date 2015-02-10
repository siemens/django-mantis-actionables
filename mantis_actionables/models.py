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

from datetime import datetime

from django.utils import timezone

from dingos.models import InfoObject, Fact, FactValue, Identifier

class Action(models.Model):

    user = models.ForeignKey(User,
                             # We allow this to be null to mark
                             # actions carried out by the system
                             null=True)

    comment = models.TextField(blank=True)


class Source(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)

    # If the source is MANTIS, we populate the following fields:

    iobject = models.ForeignKey(InfoObject,
                                null=True,
                                related_name='actionable_thru')
    iobject_fact = models.ForeignKey(Fact,
                                     null=True,
                                     related_name='actionable_thru')

    iobject_factvalue = models.ForeignKey(FactValue,
                                          null=True,
                                          related_name='actionable_thru')

    top_level_iobject = models.ForeignKey(InfoObject,related_name='related_actionable_thru')

    # If the source is a manual import, we reference the Import Info

    import_info = models.ForeignKey("ImportInfo",
                                    null=True,
                                    related_name = 'actionable_thru')

    # Classification of origin

    ORIGIN_UNCERTAIN = 0
    ORIGIN_PUBLIC = 1
    ORIGIN_VENDOR = 2
    ORIGIN_PARTNER = 3
    ORIGIN_INTERNAL_UNCHECKED = 4
    ORIGIN_INTERNAL_CHECKED = 5

    ORIGIN_KIND = ((ORIGIN_UNCERTAIN, "Uncertain"),
                     (ORIGIN_PUBLIC, "Public"),
                     (ORIGIN_VENDOR, "Provided by vendor"),
                     (ORIGIN_PARTNER, "Provided by partner"),
                     (ORIGIN_INTERNAL_UNCHECKED, "Internal (automated input)"),
                     (ORIGIN_INTERNAL_CHECKED, "Internal (manually selected)"),
    )



    origin = models.SmallIntegerField(choices=ORIGIN_KIND,
                                      help_text = "Chose 'internal (automated input)' for information "
                                                  "stemming from automated mechanism such as sandbox reports etc.")


    TLP_UNKOWN = 0
    TLP_WHITE = 10
    TLP_GREEN = 20
    TLP_AMBER = 30
    TLP_RED = 40

    TLP_KIND = ((TLP_UNKOWN,"Unknown"),
                (TLP_WHITE,"White"),
                (TLP_GREEN,"Green"),
                (TLP_AMBER,"Amber"),
                (TLP_RED,"Red"),
    )

    TLP_COLOR_CSS = {
        TLP_UNKOWN : "gray",
        TLP_WHITE : "white",
        TLP_GREEN : "green",
        TLP_AMBER : "amber",
        TLP_RED : "red"
    }

    tlp = models.SmallIntegerField(choices=TLP_KIND,
                                   default=TLP_UNKOWN)

    url = models.URLField(blank=True)


    # Sources can be linked to different models:
    # - singleton Observables
    # - IDS Signatures

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    yielded = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('iobject','iobject_fact','iobject_factvalue','top_level_iobject','content_type','object_id')


INF_TIME = datetime.max.replace(tzinfo=timezone.utc)
NULL_TIME = datetime.min.replace(tzinfo=timezone.utc)

def get_inf_time():

    return INF_TIME

def get_null_time():

    return NULL_TIME

class Status(models.Model):

    false_positive = models.NullBooleanField(help_text = "If true, the associated information (usually a "
                                                         "singleton observable) is regarded as false positive"
                                                         "and never used for detection, no matter what the "
                                                         "other status fields say")


    active = models.BooleanField(default = True,
                                 help_text = "If true, the associated information is to be used for detection")

    active_from = models.DateTimeField(default = get_null_time)
    active_to = models.DateTimeField(default = get_inf_time)

    #Field to store tags, seperated by ',', when Django 1.8 released replaced by ArrayField
    #https://docs.djangoproject.com/en/dev/ref/contrib/postgres/fields
    tags = models.TextField(blank=True,default='')

    PRIORITY_UNCERTAIN = 0
    PRIORITY_LOW = 10
    PRIORITY_MEDIUM = 20
    PRIORITY_HIGH = 30
    PRIORITY_HOT = 40


    PRIORITY_KIND = ((PRIORITY_UNCERTAIN, "Uncertain"),
                     (PRIORITY_LOW, "Low"),
                     (PRIORITY_MEDIUM, "Medium"),
                     (PRIORITY_HIGH, "High"),
                     (PRIORITY_HOT, "Hot"),
    )

    priority = models.SmallIntegerField(choices=PRIORITY_KIND,
                                      help_text = "If set to uncertain, it is up to the receiving system"
                                                  "to derive a priority from the additional info provided"
                                                  "in the source information.")


class Status2X(models.Model):

    action = models.ForeignKey(Action,
                                related_name='status_thru')

    status = models.ForeignKey(Status,
                               related_name = 'actionable_thru')

    active = models.BooleanField(default=True)

    timestamp = models.DateTimeField(auto_now_add=True, blank=True)


    # Status can be linked to different models:
    # - singleton Observables
    # - IDS Signatures

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    marked = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return "Status2X: id %s, active %s, status_id %s, marked_id %s" % (self.id,self.active,self.status_id,self.marked.id)

def createStatus(**kwargs):

    new_status, created = Status.objects.get_or_create(false_positive=False,
                                                      active=True,
                                                      priority=Status.PRIORITY_UNCERTAIN)
    return new_status

def updateStatus(status_obj,**kwargs):
    new_status, created = Status.objects.get_or_create(false_positive=status_obj.false_positive,
                                                       active=status_obj.active,
                                                       priority=status_obj.priority)
    return (new_status,created)


class SingletonObservableType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

class SingletonObservableSubtype(models.Model):
    name = models.CharField(max_length=255,blank=True)
    description = models.TextField(blank=True)

class SingletonObservable(models.Model):
    type = models.ForeignKey(SingletonObservableType)
    subtype = models.ForeignKey(SingletonObservableSubtype,null=True)
    value = models.CharField(max_length=2048)

    status_thru = generic.GenericRelation(Status2X,related_query_name='singleton_observables')

    sources = generic.GenericRelation(Source,related_query_name='singleton_observables')

    actionable_tags = generic.GenericRelation('ActionableTag2X',related_query_name='singleton_observables')

    mantis_tags = models.TextField(blank=True,default='')

    class Meta:
        unique_together = ('type', 'subtype', 'value')


class SignatureType(models.Model):
    name = models.CharField(max_length=255)


class IDSSignature(models.Model):
    type = models.ForeignKey(SignatureType)
    value = models.TextField()

    status_thru = generic.GenericRelation(Action,related_query_name='singleton_observables')

    sources = generic.GenericRelation(Source,related_query_name='singleton_observables')

    class Meta:
        unique_together = ('type', 'value')


class ImportInfo(models.Model):
    user = models.ForeignKey(User,
                             # We allow this to be null to mark
                             # imports carried out by the system
                             null=True)

    #iobject_identifier = models.ForeignKey(Identifier,
    #                                       null=True,
    #                                       help_text="If provided, should point to the identifier"
    #                                                 " of a STIX Incident object")

    comment = models.TextField(blank=True)


class Context(models.Model):
    name = models.CharField(max_length=40)

class TagName(models.Model):
    name = models.CharField(max_length=40)

class ActionableTag(models.Model):
    context = models.ForeignKey(Context,
                                null=True)
    tag = models.ForeignKey(TagName)

class ActionableTag2X(models.Model):

    actionable_tag = models.ForeignKey(ActionableTag,
                                related_name='actionable_tag_thru')


    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    tagged = generic.GenericForeignKey('content_type', 'object_id')


class ActionableTaggingHistory(models.Model):
    ADD = 0
    REMOVE = 1
    ACTIONS = [
        (ADD,'Added'),
        (REMOVE,'Removed')
    ]

    tag = models.ForeignKey(ActionableTag,related_name='actionable_tag_history')

    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.SmallIntegerField(choices=ACTIONS)
    user = models.ForeignKey(User,related_name='actionable_tagging_history',null=True)
    comment = models.TextField(blank=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    tobject = generic.GenericForeignKey('content_type', 'object_id')







    # Status can be linked to different models:
    # - singleton Observables
    # - IDS Signatures

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    marked = generic.GenericForeignKey('content_type', 'object_id')

