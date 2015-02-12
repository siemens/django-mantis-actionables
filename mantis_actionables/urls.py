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
from .views import ActionablesTableStandardSource, \
    ActionablesTableStatusSource, \
    ActionablesContextView, \
    ActionablesTagHistoryView

urlpatterns = patterns(
    'mantis_actionables.views',
    url(r'^imports/$', 'imports', name='imports'),
    #url(r'^refresh/$', 'refresh', name='refresh'),
    url(r'^tbl_data/standard$', ActionablesTableStandardSource.as_view(), name='table_data_source'),
    url(r'^tbl_data/status$', ActionablesTableStatusSource.as_view(), name='table_data_source_status'),
    url(r'^status_infos/$', 'status_infos', name='status_infos'),
    url(r'^context/(?P<context_name>[a-zA-Z0-9_\-]*)', ActionablesContextView.as_view(), name='actionables_context_view'),
    url(r'^history/(?P<tag_context>[a-zA-Z0-9_\-]*)', ActionablesTagHistoryView.as_view(), name='actionables_tag_history_view')
    #url(r'^tbl_data_export$', 'table_data_source_export', name='table_data_source_export'),
)
