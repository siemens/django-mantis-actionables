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

from menu import Menu, MenuItem
from django.core.urlresolvers import reverse


Menu.add_item("mantis_main",
              MenuItem("Actionables",
                       reverse("actionables_imports"),
                       weight = 5,
                       check = lambda request: request.user.is_authenticated(),
                       children = (
                           MenuItem("Import Sources", reverse("actionables_all_imports"), weight = 5 ),
                           MenuItem("Status Infos", reverse("actionables_all_status_infos"), weight = 5 ),
                           MenuItem("Investigations", reverse("actionables_context_list"), weight = 5 ),
                           MenuItem("Dashboard", reverse("mantis_dashboard:index"), weight = 5 ),
                           MenuItem("Bulk Search", reverse("mantis_dashboard:bulk_search"), weight = 10 )
                       )
                   )
)
