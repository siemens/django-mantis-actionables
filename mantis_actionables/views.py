__author__ = 'Philipp Lang'

from dingos.view_classes import BasicJSONView

from . import DASHBOARD_CONTENTS

class DashboardTableSource(BasicJSONView):
    @property
    def returned_obj(self):
        cursor = connection.cursor()
        POST = self.request.POST.copy()
        GET = self.request.GET.copy()
        #draw is a counter which is passed between the frontend and backend
        draw_val = safe_cast(POST.get('draw', 0), int, 0)
        res = {
            'draw': draw_val,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': [],
            'error': '',
            'cols': {}
        }


        # POST has the following parameters
        # http://www.datatables.net/manual/server-side#Configuration

        # We currently override the length to be fixed at 10
        POST[u'length'] = u'10'

        table_name = POST.get('table_type')
        if table_name in [table['name'].lower() for table in DASHBOARD_CONTENTS]:




            # Build the query for the data, and fetch that stuff
            q,params, res['recordsFiltered'] = datatable_query(table_name, POST)
            cursor.execute(q, params)
            for r in cursor.fetchall():
                r = list(r)
                r[1] = defaultfilters.date(r[1], "DATETIME_FORMAT")
                res['data'].append(r)

            # Fetch the column filter values
            if draw_val == 1:
                cursor.execute("SELECT DISTINCT object_type FROM mantis_dashboard_%s_view" % table_name)
                res['cols'][table_name + '_object_filter'] = [{'all': 'All'}]
                for col_type in cursor.fetchall():
                    res['cols'][table_name + '_object_filter'].append({col_type[0]: col_type[0]})
                res['cols'][table_name + '_namespace_filter'] = [{'all': 'All'}]
                cursor.execute("SELECT DISTINCT namespace FROM mantis_dashboard_%s_view" % table_name)
                for col_type in cursor.fetchall():
                    res['cols'][table_name + '_namespace_filter'].append({col_type[0]: col_type[0]})

            # Num of results and total rows
            cursor.execute('SELECT COUNT(*) FROM mantis_dashboard_%s_view' % table_name)
            res['recordsTotal'] = cursor.fetchone()[0]

        return res

