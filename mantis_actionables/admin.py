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


import models
from django.contrib import admin


class ActionAdmin(admin.ModelAdmin):

    list_display = (u'id', 'user', 'comment')
    list_filter = ('user',)


class SourceAdmin(admin.ModelAdmin):

    list_display = (
        u'id',
        'timestamp',
        'iobject_identifier',
        'iobject_fact',
        'iobject_factvalue',
        'top_level_iobject_identifier',
        'import_info',
        'origin',
        'tlp',
        'url',
        'content_type',
        'object_id',
    )
    list_filter = ('timestamp', 'import_info')
    raw_id_fields = (
        'iobject_identifier',
        'iobject_fact',
        'iobject_factvalue',
        'top_level_iobject_identifier',
        'content_type',
    )

    autocomplete_lookup_fields = {
        'fk': ['iobject','iobject_fact','iobject_factvalue','top_level_iobject'],
        'm2m': [],
    }


class StatusAdmin(admin.ModelAdmin):

    list_display = (
        u'id',
        'false_positive',
        'active',
        'active_from',
        'active_to',
        'priority',
    )
    list_filter = ('active', 'active_from', 'active_to')


class Status2XAdmin(admin.ModelAdmin):

    list_display = (
        u'id',
        'action',
        'status',
        'active',
        'timestamp',
        'content_type',
        'object_id',
    )
    list_filter = ('action', 'status', 'active', 'timestamp')
    raw_id_fields = ('content_type',)


class SingletonObservableTypeAdmin(admin.ModelAdmin):

    list_display = (u'id', 'name', 'description')
    search_fields = ('name',)

class SingletonObservableSubtypeAdmin(admin.ModelAdmin):

    list_display = (u'id', 'name', 'description')
    search_fields = ('name',)


class SingletonObservableAdmin(admin.ModelAdmin):

    list_display = (u'id', 'type', 'subtype', 'value')
    list_filter = ('type',)


class SignatureTypeAdmin(admin.ModelAdmin):

    list_display = (u'id', 'name')
    search_fields = ('name',)


class IDSSignatureAdmin(admin.ModelAdmin):

    list_display = (u'content',)
    list_filter = ('content',)


#class ImportInfoAdmin(admin.ModelAdmin):

#    list_display = (u'id', 'user', 'comment')
#    list_filter = ('user',)


def _register(model, admin_class):
    admin.site.register(model, admin_class)


_register(models.Action, ActionAdmin)
_register(models.Source, SourceAdmin)
_register(models.Status, StatusAdmin)
_register(models.Status2X, Status2XAdmin)
_register(models.SingletonObservableType, SingletonObservableTypeAdmin)
_register(models.SingletonObservableSubtype, SingletonObservableSubtypeAdmin)
_register(models.SingletonObservable, SingletonObservableAdmin)
_register(models.SignatureType, SignatureTypeAdmin)
_register(models.IDSSignature, IDSSignatureAdmin)
#_register(models.ImportInfo, ImportInfoAdmin)
