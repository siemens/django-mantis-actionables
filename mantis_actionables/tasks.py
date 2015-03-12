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


from __future__ import absolute_import

import logging

from celery import shared_task

from mantis_actionables.core import crowdstrike


logger = logging.getLogger(__name__)


@shared_task
def async_export_to_actionables(top_level_iobj_identifier_pk,
                                top_level_iobj_pk,
                                export_results,
                                graph=None,
                                user=None):
    from mantis_actionables.mantis_import import import_singleton_observables_from_export_result

    import_singleton_observables_from_export_result(top_level_iobj_identifier_pk,
                                                    top_level_iobj_pk,
                                                    export_results,
                                                    graph=graph,
                                                    user=user)


@shared_task
def async_tag_transfer_into_actionables(*args,**kwargs):
    from mantis_actionables.mantis_import import update_and_transfer_tags

    update_and_transfer_tags(*args,**kwargs)


@shared_task
def import_crowdstrike_csv(csv_file):
    crowdstrike.import_crowdstrike_csv(csv_file)
