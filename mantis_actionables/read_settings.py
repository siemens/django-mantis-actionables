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


import mantis_actionables


def read_from_conf(name):
    if settings.configured and 'MANTIS_ACTIONABLES' in dir(settings):
        default_value = getattr(mantis_actionables,"MANTIS_ACTIONABLES_%s" % name)

        setattr(mantis_actionables,"MANTIS_ACTIONABLES_%s" % name,
                settings.MANTIS_ACTIONABLES.get('name', default_value))


read_from_conf('STIX_REPORT_FAMILY_AND_TYPES')
read_from_conf('MANTIS_ACTIONABLES_ACTIVE_EXPORTERS')
read_from_conf('MANTIS_ACTIONABLES_DASHBOARD_CONTENTS')
read_from_conf('MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX')
read_from_conf('MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH')
read_from_conf('MANTIS_ACTIONABLES_SRC_META_DATA_FUNCTION_PATH')




