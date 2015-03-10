# Copyright (c) Siemens AG, 2013
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


import django_filters

from dingos.filter import ExtendedDateRangeFilter,create_order_keyword_list

from .models import Context, SingletonObservable



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


