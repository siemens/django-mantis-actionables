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

import importlib

from mantis_actionables import MANTIS_ACTIONABLES_STATUS_CREATION_FUNCTION_PATH, \
                               MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH

from mantis_actionables.models import Status



def createStatus(*args,**kwargs):
    if MANTIS_ACTIONABLES_STATUS_CREATION_FUNCTION_PATH:
        mod_name, func_name = MANTIS_ACTIONABLES_STATUS_CREATION_FUNCTION_PATH.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        create_status_function = getattr(mod,func_name)
        return create_status_function(*args,**kwargs)
    else:
        new_status, created = Status.objects.get_or_create(false_positive=False,
                                                           active=True,
                                                           priority=Status.PRIORITY_UNCERTAIN)
        return new_status

def updateStatus(status,*args,**kwargs):
    if MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH:
        mod_name, func_name = MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        update_status_function = getattr(mod,func_name)
        return update_status_function(status,*args,**kwargs)
    else:
        new_status, created = Status.objects.get_or_create(false_positive=status.false_positive,
                                                           active=status.active,
                                                           priority=status.priority)
        return (new_status,created)
