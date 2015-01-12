__author__ = 'Philipp Lang'

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q

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

def getTableColumns(count):
    if count == 6:
        cols = {
            0: 'sources__timestamp',
            1: 'type__name',
            2: 'value',
            3: 'sources__tlp',
            4: 'sources__top_level_iobject__identifier__namespace__uri',
            5: 'sources__top_level_iobject__name'
        }
    elif count == 5:
        cols = {
            0: 'sources__timestamp',
            1: 'value',
            2: 'sources__tlp',
            3: 'sources__top_level_iobject__identifier__namespace__uri',
            4: 'sources__top_level_iobject__name'
        }
    else:
        #exception, wrong column count
        pass
    return cols

def datatable_query(table_name, post):
    post_dict = parser.parse(str(post.urlencode()))

    # Collect prepared statement parameters in here
    params = []

    cols = getTableColumns(max(post_dict['columns'])+1)

    # Base query
    table = DASHBOARD_CONTENTS[table_name]
    if table['basis'] == 'SingletonObservable':
        base = SingletonObservable.objects
        types = table['types']
        type_ids = []
        if isinstance(types,str):
            types = [types]
        for type in types:
            try:
                type_ids.append(singleton_observable_types[type])
            except KeyError:
                continue
        if type_ids:
            q = base.filter(type_id__in=type_ids).values_list(*(cols.values()))
            q_count = base.filter(type_id__in=type_ids).count()
        else:
            return (base.none(),0)

    # Treat the filter values (WHERE clause)
    for x in post_dict.items():
        print x
    col_filters = []
    for colk, colv in post_dict.get('columns', {}).iteritems():
        srch = colv.get('search', False)
        print srch
        if not srch:
            continue
        srch = srch.get('value', False)

        if not srch or srch.lower()=='all':
            continue
        # srch should have a value
        col_filters.append({
            cols[colk] + '__exact' : srch
        })

    if col_filters:
        queries = [Q(**filter) for filter in col_filters]
        query = queries.pop()

        # Or the Q object with the ones remaining in the list
        for item in queries:
            query &= item

        # Query the model
        q = q.filter(query)


    col_search = []
    # The search value
    sv = post_dict.get('search', {})
    sv = str(sv.get('value', '')).strip()
    if sv != '':
        for n,c in cols.iteritems():
            if post_dict['columns'][n]['searchable'] == "true":
                col_search.append({
                    c + '__contains' : sv
                })

    print "#####################"
    for x in col_search:
        print x
    if col_search:
        queries = [Q(**filter) for filter in col_search]
        query = queries.pop()

        # Or the Q object with the ones remaining in the list
        for item in queries:
            query |= item

        # Query the model
        q = q.filter(query)


    # Treat the ordering of columns
    order_cols = []
    for colk, colv in post_dict.get('order', {}).iteritems():
        scol = colv.get('column', 0)
        scol = cols.get(scol)
        if not scol:
            scol = cols[0]
        sdir = colv.get('dir')
        if sdir == 'desc':
            order_cols.append('-' + scol)
        else: #asc + fallback
            order_cols.append(scol)
    if order_cols:
        q = q.order_by(*order_cols)

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

    return (q,q_count)

class ActionablesTableSource(BasicJSONView):

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
            q,res['recordsFiltered'] = datatable_query(table_name, POST)
            for row in q:
                res['data'].append(row)

            # Fetch the column filter values
            if draw_val == 1:
                res['cols'][table_name + '_type_filter'] = [{'all': 'All'}]
                types = DASHBOARD_CONTENTS[table_name]['types']
                if len(types) > 1:
                    for type_name in types :
                        res['cols'][table_name + '_type_filter'].append({type_name: type_name})
                res['cols'][table_name + '_tlp_filter'] = [{'all': 'All'}]

            # Num of results and total rows
            #TODO enable filtering
            res['recordsTotal'] = res['recordsFiltered']
        return res

def index(request):
    content_dict = {
        'title' : 'MANTIS Actionables Dashboard',
        'tables' : []
    }
    for id,table in DASHBOARD_CONTENTS.items():
        name = table['name']
        show_type = table['show_type_column']
        content_dict['tables'].append((name,id,show_type))
    return render_to_response('mantis_actionables/index.html', content_dict, context_instance=RequestContext(request))