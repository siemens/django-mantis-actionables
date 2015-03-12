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

from django.conf import settings

import importlib

import mantis_actionables

import logging

logger = logging.getLogger(__name__)

def read_from_conf(name):
    if settings.configured and 'MANTIS_ACTIONABLES' in dir(settings):
        default_value = getattr(mantis_actionables,"MANTIS_ACTIONABLES_%s" % name)
        final_value = settings.MANTIS_ACTIONABLES.get(name, default_value)
        setattr(mantis_actionables,"MANTIS_ACTIONABLES_%s" % name, final_value)
read_from_conf('STIX_REPORT_FAMILY_AND_TYPES')
read_from_conf('ACTIVE_EXPORTERS')
read_from_conf('DASHBOARD_CONTENTS')
read_from_conf('CONTEXT_TAG_REGEX')
read_from_conf('STATUS_UPDATE_FUNCTION_PATH')
read_from_conf('SRC_META_DATA_FUNCTION_PATH')




