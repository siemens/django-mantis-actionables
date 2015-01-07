__author__ = 'Philipp Lang'

from django.shortcuts import render_to_response
from django.template import RequestContext

from querystring_parser import parser

from dingos.view_classes import BasicJSONView

from . import DASHBOARD_CONTENTS
from .models import SingletonObservable
from .mantis_import import singleton_observable_types

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default

def getTableColumns(table):
        return {
            0: 'sources__timestamp',
            1: 'type__name',
            2: 'value',
            3: 'sources__tlp',
            #TODO replace with MANTIS iobject info
            4: 'id',
            5: 'type_id'
    }


def datatable_query(table_name, post):
    post_dict = parser.parse(str(post.urlencode()))
    # Collect prepared statement parameters in here
    params = []

    cols = getTableColumns(table_name)

    # Base query
    s_values = ",".join(cols.values())
    table = DASHBOARD_CONTENTS[table_name]
    if table['basis'] == 'SingletonObservable':
        type_ids = []
        for type in table['types']:
            type_ids.append(singleton_observable_types[type])
        if type_ids:
            q = SingletonObservable.objects.filter(type_id__in=type_ids).values_list(*cols)
            q_count = SingletonObservable.objects.filter(type_id__in=type_ids).count()

    # Treat the filter values (WHERE clause)
    col_filters = []
    for colk, colv in post_dict.get('columns', {}).iteritems():
        srch = colv.get('search', False)
        if not srch:
            continue
        srch = srch.get('value', False)
        if not srch or srch.lower()=='all':
            continue
        # srch should have a value
        col_filters.append(cols[colk+1] + '=%s')
        params.append(srch)

    col_search = []
    # The search value
    sv = post_dict.get('search', {})
    sv = str(sv.get('value', '')).strip()
    if sv!='':
        for n,c in cols.iteritems():
            col_search.append( c + '::text ILIKE %s')
            params.append('%'+sv+'%')

    if col_filters or col_search:
        ads = " WHERE "
        ws = []
        if col_filters:
            ws.append("(" + " AND ".join(col_filters) + ")")
        if col_search:
            ws.append("(" + " OR ".join(col_search) + ")")

        ads = ads + " AND ".join(ws)

        q = q + ads
        q_count = q_count + ads



    # Treat the ordering of columns
    sort_cols = []
    for colk, colv in post_dict.get('order', {}).iteritems():
        scol = colv.get('column', 0)
        scol = cols.get(scol)
        if not scol:
            scol = cols[0]
        sdir = colv.get('dir')
        if sdir not in ['asc','desc']:
            sdir = 'asc'

        sort_cols.append( scol + ' ' + sdir.upper())
    if sort_cols:
        ads = " ORDER BY " + " ,".join(sort_cols)
        q = q + ads



    num_filtered = c.fetchone()[0]


    # Treat the paging/limit
    length = safe_cast(post_dict.get('length'), int, 10)
    if length<-1:
        length = 10
    start = safe_cast(post_dict.get('start'), int, 0)
    if start<0:
        start = 0
    if length>0:
        q = q[start:start+length]
        params.append(length)
        params.append(start)

    return (q, params, q_count)

class DashboardTableSource(BasicJSONView):

    @property
    def returned_obj(self):
        POST = self.request.POST.copy()
        GET = self.request.GET.copy()
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
        if table_name in DASHBOARD_CONTENTS.keys():



            # Build the query for the data, and fetch that stuff
            q,params, res['recordsFiltered'] = datatable_query(table_name, POST)
            for row in q:
                res['data'].append(row)

            # # Fetch the column filter values
            # if draw_val == 1:
            #     cursor.execute("SELECT DISTINCT object_type FROM mantis_dashboard_%s_view" % table_name)
            #     res['cols'][table_name + '_object_filter'] = [{'all': 'All'}]
            #     for col_type in cursor.fetchall():
            #         res['cols'][table_name + '_object_filter'].append({col_type[0]: col_type[0]})
            #     res['cols'][table_name + '_namespace_filter'] = [{'all': 'All'}]
            #     cursor.execute("SELECT DISTINCT namespace FROM mantis_dashboard_%s_view" % table_name)
            #     for col_type in cursor.fetchall():
            #         res['cols'][table_name + '_namespace_filter'].append({col_type[0]: col_type[0]})

            # Num of results and total rows
            #TODO enable filtering
            res['recordsTotal'] = res['recordsFiltered']

        return res

def index(request):
    content_dict = {
        'title' : 'MANTIS Actionables Dashboard',
        'tables' : []
    }
    for id,table in DASHBOARD_CONTENTS:
        name = table['name']
        show_type = table['show_type_column']
        content_dict['tables'].append((name,id,show_type))
    return render_to_response('mantis_actionables/index.html', content_dict, context_instance=RequestContext(request))