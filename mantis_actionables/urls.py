# Copyright (c) Siemens AG, 2014
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

# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import SingletonObservablesWithSourceDataProvider, \
    SingeltonObservablesWithSourceOneTableDataProvider, \
    SingletonObservablesWithStatusDataProvider, \
    SingletonObservablesWithStatusOneTableDataProvider, \
    ActionablesContextView, \
    ActionablesContextList, \
    ActionablesContextEditView, \
    ActionablesTagHistoryView


urlpatterns = patterns(
    'mantis_actionables.views',
    url(r'^imports/$', 'imports', name='actionables_imports'),
    url(r'^all_imports/$', 'all_imports', name='actionables_all_imports'),
    url(r'^status_infos/$', 'status_infos', name='actionables_status_infos'),
    url(r'^all_status_infos/$', 'all_status_infos', name='actionables_all_status_infos'),
    #url(r'^refresh/$', 'refresh', name='refresh'),
    url(r'^tbl_data/all_imports$', SingeltonObservablesWithSourceOneTableDataProvider.as_view(), name='table_data_source'),
    url(r'^tbl_data/standard$', SingletonObservablesWithSourceDataProvider.as_view(), name='table_data_source'),
    url(r'^tbl_data/status$', SingletonObservablesWithStatusDataProvider.as_view(), name='table_data_source_status'),
    url(r'^tbl_data/all_status_infos$', SingletonObservablesWithStatusOneTableDataProvider.as_view(), name='table_data_source_status'),
    url(r'^context/(?P<context_name>[a-zA-Z0-9_\-]+)/?$', ActionablesContextView.as_view(), name='actionables_context_view'),
    url(r'^context/(?P<context_name>[a-zA-Z0-9_\-]+)/edit$', ActionablesContextEditView.as_view(), name='actionables_context_edit_view'),
    url(r'^context/?$', ActionablesContextList.as_view(), name='actionables_context_list'),
    url(r'^context/(?P<context_name>[a-zA-Z0-9_\-]+)/history$', ActionablesTagHistoryView.as_view(), name='actionables_context_history_view'),
    #url(r'^tbl_data_export$', 'table_data_source_export', name='table_data_source_export'),



)
