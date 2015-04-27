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

from django import forms

import django_filters

from django.forms import widgets

from dingos.filter import ExtendedDateRangeFilter,create_order_keyword_list

from .models import Context, SingletonObservable, ImportInfo

from django.db.models import Q

from django_filters import Filter

from django.utils import six

from django_filters.fields import Lookup


class MultiFilter(Filter):

    #
    # Code below taken from https://github.com/alex/django-filter
    # Copyright and license:
    # (c) Alex Gaynor and individual contributors.
    # All rights reserved.
    #
    # Redistribution and use in source and binary forms, with or without
    # modification, are permitted provided that the following conditions are met:
    #
    #  * Redistributions of source code must retain the above copyright notice, this
    #    list of conditions and the following disclaimer.
    #  * Redistributions in binary form must reproduce the above copyright notice,
    #    this list of conditions and the following disclaimer in the documentation
    #    and/or other materials provided with the distribution.
    #  * The names of its contributors may not be used to endorse or promote products
    #    derived from this software without specific prior written permission.
    #
    # THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
    # ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    # WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    # DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
    # ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
    # (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
    # LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
    # ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
    # (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    # SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


    def filter(self, qs, value):

        if isinstance(value, Lookup):
            lookup = six.text_type(value.lookup_type)
            value = value.value
        else:
            lookup = self.lookup_type
        if value in ([], (), {}, None, ''):
            return qs
        method = qs.exclude if self.exclude else qs.filter
        # Start modification
        if '__OR__' in self.name:
            # Below is our modification that allows to query two different columns at the same time
            # joined by an OR
            names = self.name.split('__OR__')
            q_obj = Q(**{'%s__%s' % (names[0], lookup): value})
            for name in names[1:]:
                q_obj = q_obj | Q(**{'%s__%s' % (name, lookup): value})
            qs = method(q_obj)
        else:
            qs = method(**{'%s__%s' % (self.name, lookup): value})

        if self.distinct:
            qs = qs.distinct()
        return qs


class CharMultiFilter(MultiFilter):
    pass

class ActionablesContextFilter(django_filters.FilterSet):

    name = django_filters.CharFilter(lookup_type='icontains',
                                     label='Name contains')
    title = django_filters.CharFilter(lookup_type='icontains',
                                     label='Title contains')

    timestamp = ExtendedDateRangeFilter(label="Creation Timestamp")

    class Meta:
        order_by = create_order_keyword_list(['timestamp','name','title'])
        model = Context
        fields = ['name','title','timestamp']


class ImportInfoFilter(django_filters.FilterSet):

    namespace__uri = django_filters.CharFilter(lookup_type='icontains',
                                                label='ID-Namespace contains')



    name = django_filters.CharFilter(lookup_type='icontains',
                                     label='Name contains')

    timestamp = ExtendedDateRangeFilter(label="Source Creation Timestamp")

    create_timestamp = ExtendedDateRangeFilter(label="Import Timestamp")

    class Meta:
        order_by = create_order_keyword_list(['timestamp','create_timestamp','name','title'])
        model = ImportInfo
        fields = ['name','namespace__uri','timestamp','create_timestamp']


class BulkInvestigationFilter(django_filters.FilterSet):

    type__name = django_filters.CharFilter(lookup_type='icontains',
                                           label='Type contains')
    subtype__name = django_filters.CharFilter(lookup_type='icontains',
                                              label='Subtype')

    class Meta:
        order = ['type__name','subtype__name','value']
        order_by = create_order_keyword_list(order)
        model = SingletonObservable
        fields = ['type__name','subtype__name','value']


class SingletonObservablesFilter(django_filters.FilterSet):

    type__name = django_filters.CharFilter(lookup_type='icontains',
                                     label='Type contains')
    subtype__name = django_filters.CharFilter(lookup_type='icontains',
                                              label='Subtype')
    value = django_filters.CharFilter(lookup_type='icontains',
                                              label='Value contains')

    class Meta:
        order_by = create_order_keyword_list(['type__name','subtype__name','value'])
        model = SingletonObservable
        fields = ['type__name','subtype__name','value']


class ExtendedSingletonObservablesFilter(django_filters.FilterSet):

    type__name = django_filters.CharFilter(lookup_type='icontains',
                                     label='Type contains')
    subtype__name = django_filters.CharFilter(lookup_type='icontains',
                                              label='Subtype')
    value = django_filters.CharFilter(lookup_type='icontains',
                                              label='Value contains')
    sources__import_info__name__OR__sources__top_level_iobject_identifier__latest__name = CharMultiFilter(lookup_type='icontains',
                                                           label='Report name contains')

    sources__import_info__name = django_filters.CharFilter(label='',widget=widgets.HiddenInput())
    sources__top_level_iobject_identifier__latest__name = django_filters.CharFilter(label='',widget=widgets.HiddenInput())

    test = forms.CharField(required=False,label="Test")
    
    class Meta:
        order_by = create_order_keyword_list(['type__name','subtype__name','value'])
        model = SingletonObservable
        fields = ['type__name','subtype__name','value','sources__import_info__name','sources__top_level_iobject_identifier__latest__name']


    #def clean(self):
    #    cleaned_data = super(ExtendedSingletonObservablesFilter, self).clean()
    #    cleaned_data['sources__top_level_iobject_identifier__latest__name'] = cleaned_data.get("sources__import_info__name")
    #    print "CLEANED %s" % cleaned_data
    #    return cleaned_data