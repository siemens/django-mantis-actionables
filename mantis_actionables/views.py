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

# -*- coding: utf-8 -*-

import logging

import datetime
from querystring_parser import parser

from django.core.urlresolvers import reverse

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.html import escape

from django.contrib import messages
from taggit.models import Tag
from dingos import DINGOS_TEMPLATE_FAMILY
from dingos.forms import InvestigationForm
from dingos.view_classes import BasicJSONView, BasicTemplateView, BasicFilterView, BasicUpdateView, BasicDetailView,BasicListView
from dingos.views import getTagsbyModel

from dingos.core.utilities import listify, set_dict
from dingos.templatetags.dingos_tags import show_TagDisplay


from .models import SingletonObservable,SingletonObservableType,Source,ActionableTag,TagName,ActionableTag2X,ActionableTaggingHistory,Context,Status,ImportInfo,Status2X
from .filter import ActionablesContextFilter, SingletonObservablesFilter, ImportInfoFilter

from .forms import ContextEditForm

from dingos.models import vIO2FValue, Identifier

from .tasks import actionable_tag_bulk_action

logger = logging.getLogger(__name__)

#content_type_id
CONTENT_TYPE_SINGLETON_OBSERVABLE = ContentType.objects.get_for_model(SingletonObservable)

#init column_dict
COLS = {}


def my_escape(value):
    if not value:
        return value
    else:
        return(escape(value))


def fillColDict(colsDict,cols):
    for index,col in zip(range(len(cols)),cols):
        colsDict[index] = col


def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default


def datatable_query(post, **kwargs):

    post_dict = parser.parse(str(post.urlencode()))

    # Collect prepared statement parameters in here
    params = []
    cols = kwargs.pop('query_columns')
    display_cols = kwargs.pop('display_columns')
    config = kwargs.pop('query_config')
    
    q = config['base'].objects
    base_filters = config.get('filters',[])

    count =config.get('count',True)
    cols = dict((x, y[0]) for x, y in cols.items())

    display_cols = dict((x, y[0]) for x, y in display_cols.items())

    # extend query by kwargs['filter']
    for filter in base_filters:
        q = q.filter(**filter)

    if count:
        q_count_all = q.count()
    else:
        q_count_all = -1

    # Treat the filter values (WHERE clause)
    col_filters = []
    for colk, colv in post_dict.get('columns', {}).iteritems():
        srch = colv.get('search', False)
        if not srch:
            continue
        srch = srch.get('value', False)

        if not srch or (type(srch) == type(basestring) and srch.lower()=='all'):
            continue
        # srch should have a value
        col_filters.append({
            display_cols[colk] + '__icontains' : srch
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
        for n,c in display_cols.iteritems():

            if post_dict['columns'][n]['searchable'] == "true":
                col_search.append({
                    c + '__icontains' : sv
                })

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

    if True:
        q_count_filtered = q.count()
    else:
        q_count_filtered = 100
    # Treat the paging/limit
    length = safe_cast(post_dict.get('length'), int)
    start = safe_cast(post_dict.get('start'), int, 0)
    if start<0:
        start = 0
    if length>0:
        q = q[start:start+length]
        params.append(length)
        params.append(start)

    #sources__id for join on sources table
    #values_list() has to be called here, otherwise the query isn't correct
    q = q.values_list(*(cols.values()))

    #return (q,-1,-1)
    return (q, q_count_all,q_count_filtered)


class BasicTableDataProvider(BasicJSONView):
    #add here filters and select_related statements to the base query
    filter = {}
    select_related = []

    table_spec = None

    table_spec_map = {}

    #pagination length
    table_rows = 10

    #column ids (starting with 0 = first column) where a column based filter should be displayed
    column_filter = []

    @classmethod
    def get_cols_dict(cls,table_name):

        table_name = table_name.lower().replace(' ','_')
        provider_specific_dict = COLS.setdefault(cls.__name__,{})
        return provider_specific_dict.setdefault(table_name,{})


    def post(self, request, *args, **kwargs):
        POST = request.POST
        table_name = POST.get('table_type').replace(' ','_')
        logger.debug("Received data query from user %s for table %s" % (request.user,table_name))
        return super(BasicTableDataProvider,self).post(request,*args,**kwargs)

    view_name = ""

    @classmethod
    def qualified_view_name(cls):
        return "actionables_dataprovider_%s" % cls.view_name

    curr_cols = None

    def get_curr_cols(self,table_name):
        if self.curr_cols == None:
            self.init_data()

        table_name = table_name.lower().replace(' ','_')

        return COLS[self.__class__.__name__][table_name]

    @classmethod
    def init_data(cls):
        for table_name in cls.table_spec:
            table_name = table_name.lower().replace(' ','_')
            this_table_spec = cls.table_spec.get(table_name)
            cls.curr_cols = cls.get_cols_dict(table_name)
            if not cls.curr_cols:
                #init default column_dicts
                query_columns = cls.curr_cols.setdefault('query_columns',{})
                display_columns = cls.curr_cols.setdefault('display_columns',{})
                query_config = cls.curr_cols.setdefault('query_config',{})

                query_config['base'] = this_table_spec['model']
                query_config['filters'] = this_table_spec.get('filters',[])
                query_config['count'] = this_table_spec.get('count',True)

                COLS_TO_QUERY = this_table_spec['COMMON_BASE'] + this_table_spec['QUERY_ONLY']
                COLS_TO_DISPLAY = this_table_spec['COMMON_BASE'] + this_table_spec['DISPLAY_ONLY']

                this_table_spec['offset'] = len(this_table_spec['COMMON_BASE'])

                fillColDict(query_columns,COLS_TO_QUERY)
                fillColDict(display_columns,COLS_TO_DISPLAY)


    def postprocess(self,table_name,res,q):
        #insert fetched rows into result
        for row in q:
            res['data'].append(row)

        #treat filters
        #if res['draw'] == 1:
        #    res['cols'][table_name + '_type_filter'] = [{'all': 'All'}]
        #    types = DASHBOARD_CONTENTS[table_name]['types']
        #    if len(types) > 1:
        #        for type_name in types :
        #            res['cols'][table_name + '_type_filter'].append({type_name: type_name})

    @property
    def returned_obj(self):
        POST = self.request.POST.copy()
        if not POST:
            POST = self.request.GET.copy()
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

        table_name = POST.get('table_type','').replace(' ','_')


        config_info = self.get_curr_cols(table_name)

        kwargs = {
                'query_columns' : config_info['query_columns'],
                'display_columns' : config_info.get('display_columns',config_info['query_columns']),
                'filter' : self.filter,
                'query_config' : config_info['query_config'],
                }

        logger.debug("About to start database query for user %s for table %s" % (self.request.user,table_name))
        q,res['recordsTotal'],res['recordsFiltered'] = datatable_query(POST, **kwargs)
        q = list(q)
        logger.debug("Finished database query for user %s for table %s; %s results" % (self.request.user,table_name,len(q)))

        self.postprocess(table_name,res,q)
        logger.debug("Finished postprocessing for user %s for table %s" % (self.request.user,table_name))
        return res


def table_name_slug(table_name):
    return table_name.lower().replace(' ','_')


class SingeltonObservablesWithSourceOneTableDataProvider(BasicTableDataProvider):

    view_name = "singletons_with_source_one_table"

    table_spec =  {}

    TABLE_NAME_ALL_IMPORTS = 'Indicators by Source'

    ALL_IMPORTS_TABLE_SPEC = {
        'model' : SingletonObservable,
        'count': False,
        'COMMON_BASE' : [

                ('sources__timestamp','Source TS','0'), #0
                ('sources__tlp','TLP','0'), #1
                ('type__name','Type','0'), #2
                ('subtype__name','Subtype','0'), #3
                ('value','Value','1'), #4
                ('sources__related_stix_entities__entity_type__name','Context Type','0'), #5
                ('sources__related_stix_entities__essence','Context Info','0'), #6
            ],
        'QUERY_ONLY' : [('sources__top_level_iobject_identifier__namespace__uri','Report Source','0'), #0

                             ('sources__top_level_iobject__name','Report Name','0'), #1
                             ('sources__top_level_iobject_id','Report InfoObject PK','0'), #2
                             ('sources__import_info__namespace__uri','Report Source','0'), #3
                             ('sources__import_info__name','Report Name','0'), #4
                             ('sources__import_info_id','Report Import Info PK','0'), #5,
                             ('id','Singleton Observable PK','0') #6
                            ],
        'DISPLAY_ONLY' :  [('sources__import_info__namespace__uri','Report Source','0'),
                             ('sources__import_info__name','Report Name','0'),
                             ]
    }

    table_spec[table_name_slug(TABLE_NAME_ALL_IMPORTS)] = ALL_IMPORTS_TABLE_SPEC

    table_rows = 10

    column_filter = [2,3,4,5,7,8]

    @classmethod
    def ALL_IMPORTS_POSTPROCESSOR(cls,table_spec,res,q):
        offset = table_spec['offset']

        for row in q:
            row = [my_escape(e) for e in list(row)]

            row[1] = Source.TLP_COLOR_CSS.get(int(row[1]),"ERROR")
            if row[offset+2]:
                row[offset+1] = "<a href='%s'>%s</a>" % (reverse('url.dingos.view.infoobject',kwargs={'pk':int(row[offset+2])}),
                                                                 row[offset+1])
            else:
                row[offset+0] = row[offset+3]
                row[offset+1] = "<a href='%s'>%s</a>" % (reverse('actionables_import_info_details',kwargs={'pk':int(row[offset+5])}),
                                                                 row[offset+4])

            row[4] = "<a href='%s'>%s</a>" % (reverse('actionables_singleton_observables_details',kwargs={'pk':int(row[offset+6])}),
                                                                 row[4])

            row = row[:-5]
            res['data'].append(row)


    def postprocess(self,table_name,res,q):
        table_spec = self.table_spec[table_name]
        return self.ALL_IMPORTS_POSTPROCESSOR(table_spec,res,q)

        #treat filters
        # if res['draw'] == 1:
        #     res['cols'][table_name + '_type_filter'] = [{'all': 'All'}]
        #     types = DASHBOARD_CONTENTS[table_name]['types']
        #     if len(types) > 1:
        #         for type_name in types :
        #             res['cols'][table_name + '_type_filter'].append({type_name: type_name})
        #     res['cols'][table_name + '_tlp_filter'] = [{'all': 'All'}]
        #     res['cols'][table_name + '_ns_filter'] = [{'all' : 'All'}]
        #     namespaces = list(IdentifierNameSpace.objects.all().values_list('uri',flat=True))
        #     if len(namespaces) > 1:
        #         for ns in namespaces:
        #             res['cols'][table_name + '_ns_filter'].append({ns : ns})
        #


class SingeltonObservablesWithSourceOneTableDataProviderFilterByContext(BasicTableDataProvider):

    view_name = "singletons_with_source_one_table_contextfilter"

    table_spec =  {}

    TABLE_NAME_ALL_IMPORTS_F_CONTEXT = 'Indicators by Source filtered by context'

    ALL_IMPORTS_TABLE_SPEC_F_CONTEXT = {
        'model' : SingletonObservable,
        'count': False,
        'COMMON_BASE' : [

                ('sources__timestamp','Source TS','0'), #0
                ('sources__tlp','TLP','0'), #1
                ('type__name','Type','0'), #2
                ('subtype__name','Subtype','0'), #3
                ('value','Value','0'), #4
                ('sources__related_stix_entities__entity_type__name','Context Type','0'), #5
                ('sources__related_stix_entities__essence','Context Info','1'), #6
            ],
        'QUERY_ONLY' : [('sources__top_level_iobject_identifier__namespace__uri','Report Source','0'), #0

                             #('sources__top_level_iobject_identifier__latest__name','Report Name','0'), #1
                             #('sources__top_level_iobject_identifier__latest_id','Report InfoObject PK','0'), #2
                             ('sources__top_level_iobject__name','Report Name','0'), #1
                             ('sources__top_level_iobject_id','Report InfoObject PK','0'), #2
                             ('sources__import_info__namespace__uri','Report Source','0'), #3
                             ('sources__import_info__name','Report Name','0'), #4
                             ('sources__import_info_id','Report Import Info PK','0'), #5,
                             ('id','Singleton Observable PK','0') #6
                            ],
        'DISPLAY_ONLY' :  [('','Report Source','0'),
                             ('','Report Name','0'),
                             ]
    }

    table_spec[table_name_slug(TABLE_NAME_ALL_IMPORTS_F_CONTEXT)] = ALL_IMPORTS_TABLE_SPEC_F_CONTEXT


class UnifiedSearchSourceDataProvider(BasicTableDataProvider):
    view_name = "unified_search"

    table_spec =  {}

    TABLE_NAME_ALL_IMPORTS = 'Indicators by Source'

    TABLE_NAME_ALL_IMPORTS_F_CONTEXT = 'Indicators by Source filtered by context'

    table_spec[table_name_slug(TABLE_NAME_ALL_IMPORTS)] = SingeltonObservablesWithSourceOneTableDataProvider.ALL_IMPORTS_TABLE_SPEC

    table_spec[table_name_slug(TABLE_NAME_ALL_IMPORTS_F_CONTEXT)] = SingeltonObservablesWithSourceOneTableDataProviderFilterByContext.ALL_IMPORTS_TABLE_SPEC_F_CONTEXT


    #COLS_TO_DISPLAY = [
    #            ('iobject_identifier_uri','Namespace','0'),
    #            ('iobject_identifier_uid','Identifier','0'),
    #            ('iobject_name','Name','0'),
    #            ('term','Term','0'),
    #            ('attribute','Attribute','0'),
    #            ('value','Value','1'),
    #        ]

    TABLE_NAME_DINGOS_VALUES = 'General Value Search'

    DINGOS_VALUES_TABLE_SPEC = {
        'model' : vIO2FValue,
        'filters' : [{'iobject__latest_of__isnull':False}],
        'count' : False,
        'COMMON_BASE' : [
                ('iobject_identifier_uri','Namespace','0'),
                ('iobject_identifier_uid','Identifier','0'),
                ('iobject_name','Name','0'),
                ('term','Term','0'),
                ('attribute','Attribute','0'),
                ('value','Value','1'),
            ],
        'QUERY_ONLY' : [('iobject_id','XXX',0)],

        'DISPLAY_ONLY' :  []

    }

    table_spec[table_name_slug(TABLE_NAME_DINGOS_VALUES)] = DINGOS_VALUES_TABLE_SPEC

    TABLE_NAME_INFOBJECT_IDENTIFIER_UID = 'InfoObject Identifiers and Names'

    INFOOBJECT_IDENTIFIER_UID_TABLE_SPEC = {
        'model' : Identifier,
        'filters' : [{'latest__isnull':False}],
        'count': False,
        'COMMON_BASE' : [
                ('namespace__uri','Namespace','0'),
                ('uid','Identifier','1'),
                ('latest__name','Name','1'),
            ],
        'QUERY_ONLY' : [('latest__id','XXX',0)],

        'DISPLAY_ONLY' :  []

    }

    table_spec[table_name_slug(TABLE_NAME_INFOBJECT_IDENTIFIER_UID)] = INFOOBJECT_IDENTIFIER_UID_TABLE_SPEC

    TABLE_NAME_IMPORT_INFO_NAME = 'Import Info Names'

    IMPORT_INFO_NAME_TABLE_SPEC = {
        'model' : ImportInfo,
        'filters' : [],
        'count': False,
        'COMMON_BASE' : [
                ('create_timestamp','Import Timestamp','0'),#0
                ('namespace__uri','Namespace','0'),#1
                ('uid','Identifier','0'),#2
                ('name','Name','1'),#3
            ],
        'QUERY_ONLY' : [('id','XXX',0)],

        'DISPLAY_ONLY' :  [('tags','Tags','0')]

    }

    table_spec[table_name_slug(TABLE_NAME_IMPORT_INFO_NAME)] = IMPORT_INFO_NAME_TABLE_SPEC



    def postprocess(self,table_name,res,q):
        table_spec = self.table_spec[table_name]
        if table_name in [table_name_slug(self.TABLE_NAME_ALL_IMPORTS), table_name_slug(self.TABLE_NAME_ALL_IMPORTS_F_CONTEXT)]:
            return SingeltonObservablesWithSourceOneTableDataProvider.ALL_IMPORTS_POSTPROCESSOR(table_spec,res,q)
        elif table_name == table_name_slug(self.TABLE_NAME_DINGOS_VALUES):
            offset = table_spec['offset']
            for row in q:
                row = [my_escape(e) for e in list(row)]
                row[2] = "<a href='%s'>%s</a>" % (reverse('url.dingos.view.infoobject',kwargs={'pk':row[offset+0]}),
                                                                 row[2])
                res['data'].append(row)
        elif table_name == table_name_slug(self.TABLE_NAME_INFOBJECT_IDENTIFIER_UID):
            offset = table_spec['offset']
            for row in q:
                row = [my_escape(e) for e in list(row)]
                row[2] = "<a href='%s'>%s</a>" % (reverse('url.dingos.view.infoobject',kwargs={'pk':row[offset+0]}),
                                                                 row[2])
                res['data'].append(row)
        elif table_name == table_name_slug(self.TABLE_NAME_IMPORT_INFO_NAME):
            offset = table_spec['offset']
            import_info_pks = map(lambda x: x[offset+0],q)

            self.object2tag_map = {}
            tag_infos = ImportInfo.objects.filter(pk__in=import_info_pks).values_list('pk',
                                                                             'actionable_tags__actionable_tag__context__name',
                                                                             'actionable_tags__actionable_tag__tag__name')
            tag_map = {}

            for pk,context_name,tag_name in tag_infos:
                if context_name and context_name == tag_name:

                    set_dict(tag_map,context_name,'append',int(pk))



            for row in q:

                row = [my_escape(e) for e in list(row)]
                row[3] = "<a href='%s'>%s</a>" % (reverse('actionables_import_info_details',kwargs={'pk':row[offset+0]}),
                                                                 row[3])

                tag_list = tag_map.get(int(row[offset+0]))
                if tag_list:

                    tag_list = ", ".join(tag_list)
                else:
                    tag_list = ""
                row[4] = tag_list
                res['data'].append(row)





    table_rows = 10


class SingletonObservablesWithStatusOneTableDataProvider(BasicTableDataProvider):

    view_name = "singletons_with_status"

    TABLE_NAME_ALL_STATI = "Status information for indicators"

    ALL_STATI_TABLE_SPEC = {
        'model' : SingletonObservable,
        'filters' : [{
                  'status_thru__active' : True
                }],
        'count': False,
        'COMMON_BASE' : [
                ('status_thru__timestamp','Status Timestamp','0')  , #0
                ('status_thru__status__most_permissive_tlp','lightest TLP','0')  , #1
                ('status_thru__status__most_restrictive_tlp','darkest TLP','0')  , #2
                ('status_thru__status__max_confidence','Max confidence','0'), #3
                ('status_thru__status__best_processing','Processing','0'), #4
                ('status_thru__status__kill_chain_phases','Kill Chain','0'), #5
                ('type__name','Type','1'), #6
                ('subtype__name','Subtype','1'), #7
                ('value','Value','1'), #8
                ('actionable_tags_cache','Tags','1'), #9


            ],
        'QUERY_ONLY' : [('id','XXX',0)],
        'DISPLAY_ONLY' :  []

    }

    table_spec= {table_name_slug(TABLE_NAME_ALL_STATI):ALL_STATI_TABLE_SPEC}

    column_filter = [6,7,8,9]

    def postprocess(self,table_name,res,q):
        table_spec = self.table_spec[table_name]
        offset = table_spec['offset']

        for row in q:
            row = list([my_escape(e) for e in list(row)])
            row[1] = Status.TLP_MAP[int(row[1])]
            row[2] = Status.TLP_MAP[int(row[2])]
            row[3] = Status.CONFIDENCE_MAP[int(row[3])]
            row[4] = Status.PROCESSING_MAP[int(row[4])]

            row[8] = "<a href='%s'>%s</a>" % (reverse('actionables_singleton_observables_details',kwargs={'pk':int(row[offset+0])}),
                                                                 row[8])

            row = row[:-1]

            res['data'].append(row)



    #select_related = ['status_thru__status']


class BasicDatatableView(BasicTemplateView):


    initial_filter = ''
    data_provider_class = None

    datatables_dom = "tip"

    def get(self, request, *args, **kwargs):
        self.data_provider_class.init_data()

        return super(BasicDatatableView, self).get(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super(BasicDatatableView, self).get_context_data(**kwargs)
        context['data_view_name'] = self.data_provider_class.qualified_view_name
        context['title'] = self.title
        context['initial_filter'] = self.initial_filter
        context['table_rows'] = self.data_provider_class.table_rows
        context['column_filter'] = self.data_provider_class.column_filter
        context['tables'] = []

        context['datatables_dom'] = self.datatables_dom


        for table_name in self.table_spec:
            table_name_slug = table_name.lower().replace(' ','_')
            display_columns = COLS[self.data_provider_class.__name__][table_name_slug].get('display_columns',
                                                                                      COLS[self.data_provider_class.__name__][table_name_slug]["query_columns"])
            context['tables'].append((table_name,display_columns))

        return context


class SourceInfoView(BasicDatatableView):

    data_provider_class = SingeltonObservablesWithSourceOneTableDataProvider

    template_name = 'mantis_actionables/%s/table_base.html' % DINGOS_TEMPLATE_FAMILY


    title = 'Indicators and their sources'

    table_spec = [data_provider_class.TABLE_NAME_ALL_IMPORTS]


class StatusInfoView(BasicDatatableView):

    data_provider_class = SingletonObservablesWithStatusOneTableDataProvider

    template_name = 'mantis_actionables/%s/table_base.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Indicator Status Info'

    table_spec = [data_provider_class.TABLE_NAME_ALL_STATI]


class UnifiedSearch(BasicDatatableView):


    @property
    def initial_filter(self):
        if self.request.GET.get('search_term',False):
            return self.request.GET.get('search_term')
        else:
            return self.kwargs.get('search_term','')

    data_provider_class = UnifiedSearchSourceDataProvider

    template_name = 'mantis_actionables/%s/table_base.html' % DINGOS_TEMPLATE_FAMILY


    title = 'Unified Search'

    table_spec = [data_provider_class.TABLE_NAME_ALL_IMPORTS,
                  data_provider_class.TABLE_NAME_ALL_IMPORTS_F_CONTEXT,
                  data_provider_class.TABLE_NAME_DINGOS_VALUES,
                  data_provider_class.TABLE_NAME_INFOBJECT_IDENTIFIER_UID,
                  data_provider_class.TABLE_NAME_IMPORT_INFO_NAME]


def processActionablesTagging(data,**kwargs):
    action = data['action']
    obj_pks = data['objects']
    tags = listify(data['tags'])
    res = {}
    ACTIONS = ['add', 'remove']
    if action in ACTIONS:

        user = kwargs.pop('user',None)
        if user is None or not isinstance(user,User):
            raise ObjectDoesNotExist('no user for this action provided')

        curr_context = data.get('curr_context',None)
        if not curr_context:
            raise ObjectDoesNotExist('no context for this action found')

        user_data = data.get('user_data',None)

        if tags:
            #tag_name_obj = []
            #context,created = Context.objects.get_or_create(name=curr_context)
            if action == 'add':
                context_name_pairs = map(lambda x: (curr_context,x), tags)
                comment = '' if not user_data else user_data
                ActionableTag.bulk_action(action = 'add',
                                          context_name_pairs=context_name_pairs,
                                          thing_to_tag_pks=obj_pks,
                                          user=user,
                                          comment=comment)
                #for tag in tags:
                #    curr_tag, created = TagName.objects.get_or_create(name=tag)
                #    actionable_tag,created = ActionableTag.objects.get_or_create(context=context,
                #                                                         tag=curr_tag)
                #    tag_name_obj.append(actionable_tag)
                #    for pk in obj_pks:
                #        actionable_tag_2x,created = ActionableTag2X.objects.get_or_create(actionable_tag=actionable_tag,
                #                                                          object_id=pk,
                #                                                          content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE)

                curr_context = show_TagDisplay(tags,'actionables',isEditable=True)
                tag_html = render_to_string('dingos/%s/includes/_TagDisplay.html' % (DINGOS_TEMPLATE_FAMILY),curr_context)
                res['html'] = tag_html
                res['status'] = 0
                comment = '' if not user_data else user_data
                #ActionableTaggingHistory.bulk_create_tagging_history(action,tag_name_obj,obj_pks,user,comment)

            elif action == 'remove':
                if user_data is None:
                    res['additional'] = {
                        'dialog_id' : 'dialog-tagging-remove',
                        'msg' : 'To delete a tag, a comment is required.'
                    }
                    res['status'] = 1
                else:
                    if user_data == '':
                        res['status'] = -1
                        res['err'] = "no comment provided - tag not deleted"
                    else:
                        context_name_pairs = map(lambda x: (curr_context,x), tags)
                        comment = '' if not user_data else user_data
                        ActionableTag.bulk_action(action = 'remove',
                                          context_name_pairs=context_name_pairs,
                                          thing_to_tag_pks=obj_pks,
                                          user=user,
                                          comment=comment)
                        #for tag in tags:
                        #    curr_tag = TagName.objects.get(name=tag)
                        #    actionable_tag = ActionableTag.objects.get(context=context,
                        #                                       tag=curr_tag)
                        #    tag_name_obj.append(actionable_tag)
                        #    for pk in obj_pks:
                        #        ActionableTag2X.objects.get(actionable_tag=actionable_tag,
                        #                            object_id=pk,
                        #                            content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE).delete()
                        #ActionableTaggingHistory.bulk_create_tagging_history(action,tag_name_obj,obj_pks,user,user_data)
                        res['status'] = 0
        else:
            res['err'] = 'no tag provided'
            res['status'] = -1
    else:
        raise NotImplementedError('%s not a possible action to perform') % (action)

    return res


class ActionablesContextView(BasicFilterView):
    template_name = 'mantis_actionables/%s/ContextView.html' % DINGOS_TEMPLATE_FAMILY


    filterset_class= SingletonObservablesFilter

    allow_save_search = False

    counting_paginator = True

    @property
    def title(self):
        return self.curr_context_name

    order_by_dict = {'type':'actionable_tag_thru__singleton_observables__type__name',
                     'subtype':'actionable_tag_thru__singleton_observables__subtype__name',
                     'value': 'actionable_tag_thru__singleton_observables__value'}


    object2tag_map = {}



    def object2tags(self,object,type='SingletonObservable'):

        if not self.object2tag_map or not object:

            # Compile tag info for SingletonObservables
            self.object2tag_map = {}
            tag_infos = self.object_list.values_list('pk','actionable_tags__actionable_tag__context__name',
                                                     'actionable_tags__actionable_tag__tag__name')

            for pk,context_name,tag_name in tag_infos:
                if context_name == self.curr_context_name:
                    set_dict(self.object2tag_map,tag_name,'append',('SingletonObservable',pk))

            # Compile tag info for Top-Level-Identifiers  in sources

            iobject_pks = self.object_list.values_list('sources__top_level_iobject__identifier',flat=True)

            tag_infos = getTagsbyModel(iobject_pks,model=Identifier)

            for pk,tag_list in tag_infos.items():
                set_dict(self.object2tag_map,tag_list,'set',('Identifier',pk))

            # Compile tag info for ImportInfos in sources:

            import_info_pks = self.object_list.values_list('sources__import_info',flat=True)

            tag_infos = ImportInfo.objects.filter(pk__in=import_info_pks).values_list('pk','actionable_tags__actionable_tag__context__name',
                                                     'actionable_tags__actionable_tag__tag__name')

            for pk,context_name,tag_name in tag_infos:
                if context_name == tag_name:
                    set_dict(self.object2tag_map,tag_name,'append',('ImportInfo',pk))




        if object:

            return sorted(self.object2tag_map.get((type,object.pk),[]))






    @property
    def queryset(self):
        tagged_object_pks = ActionableTag.objects.filter(context__name=self.curr_context_name)\
                                         .filter(actionable_tag_thru__content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE)\
                                        .values_list('actionable_tag_thru__object_id',flat=True)



        return SingletonObservable.objects.filter(pk__in=tagged_object_pks).select_related('type','subtype',
                                                                                           'actionable_tags__actionable_tag__context',
                                                                                           'actionable_tags__actionable_tag__tag').\
            prefetch_related('sources__top_level_iobject_identifier__latest','sources__top_level_iobject_identifier__namespace').\
            prefetch_related('sources__iobject_identifier__latest','sources__iobject_identifier__namespace').\
            prefetch_related('sources__iobject_identifier__latest__iobject_type').\
            prefetch_related('sources__import_info','sources__import_info__namespace')




    def get_context_data(self, **kwargs):

        # recalculate tag map
        self.object2tags(None)

        context = super(ActionablesContextView, self).get_context_data(**kwargs)


        context['isEditable'] = True

        context['ContextMetaDataWidgetConfig'] = {'action_buttons' : ['edit','show_history']}
        return context

    def get(self,request, *args, **kwargs):
        self.order_by = self.order_by_dict.get(request.GET.get('o'))
        self.curr_context_name = kwargs.get('context_name')
        try:
            self.curr_context_object = Context.cached_objects.get(name=self.curr_context_name)
        except ObjectDoesNotExist:
            self.curr_context_object = None

        return super(ActionablesContextView,self).get(request, *args, **kwargs)


class ActionablesTagHistoryView(BasicTemplateView):
    template_name = 'mantis_actionables/%s/ActionTagHistoryList.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Actionable Tag History'

    tag_context = None

    possible_models = {
            SingletonObservable : ['id',
                                   'type__name',
                                   'subtype__name','value'],
        }

    def get_context_data(self, **kwargs):
        context = super(ActionablesTagHistoryView, self).get_context_data(**kwargs)

        cols_history = ['tag__tag__name','timestamp','action','user__username','content_type_id','object_id','comment']
        sel_rel = ['tag','user','content_type']
        history_q = list(ActionableTaggingHistory.objects.select_related(*sel_rel).\
                         filter(content_type_id=CONTENT_TYPE_SINGLETON_OBSERVABLE).\
                         filter(tag__context__name=self.tag_context).order_by('-timestamp').\
                         values(*cols_history))


        obj_info_mapping = {}
        for model,cols in self.possible_models.items():
            content_id = ContentType.objects.get_for_model(model).id
            setattr(self,'pks',set([x['object_id'] for x in history_q if x['content_type_id'] == content_id]))
            model_q = model.objects.filter(id__in=self.pks).values(*cols)
            current_model_map = obj_info_mapping.setdefault(content_id,{})
            for obj in model_q:

                current_model_map[obj['id']] = obj
            del self.pks
        context['mode'] = self.mode
        context['tag_context'] = self.tag_context
        context['history'] = history_q
        context['map_objs'] = obj_info_mapping
        context['map_action'] = ActionableTaggingHistory.ACTIONS

        # TODO: Displaying buttons in this widget is a hack: we need
        # a proper menu system with a context-specific menu display
        context['ContextMetaDataWidgetConfig'] = {'action_buttons' : ['edit','show_details']}
        return context

    def get(self, request, *args, **kwargs):
        self.mode = request.GET.get('mode')

        self.tag_context = kwargs.pop('context_name',None)
        self.title = "Timeline for '%s'" % self.tag_context
        try:
            self.curr_context_object = Context.cached_objects.get(name=self.tag_context)
        except ObjectDoesNotExist:
            self.curr_context_object = None

        return super(ActionablesTagHistoryView,self).get(request, *args, **kwargs)


class ActionablesContextList(BasicFilterView):
    template_name = 'mantis_actionables/%s/ContextList.html' % DINGOS_TEMPLATE_FAMILY

    title = "Context Overview"

    filterset_class= ActionablesContextFilter

    allow_save_search = False

    counting_paginator = True


class ImportInfoList(BasicFilterView):
    template_name = 'mantis_actionables/%s/ImportInfoList.html' % DINGOS_TEMPLATE_FAMILY

    title = "Import Overview"

    filterset_class= ImportInfoFilter

    allow_save_search = False

    counting_paginator = True

    object2tag_map = {}


    def object2tags(self,object):
        if not self.object2tag_map or not object:

            self.object2tag_map = {}
            tag_infos = self.object_list.values_list('pk','actionable_tags__actionable_tag__context__name',
                                                     'actionable_tags__actionable_tag__tag__name')
            for pk,context_name,tag_name in tag_infos:
                if context_name == tag_name:
                    set_dict(self.object2tag_map,tag_name,'append',pk)


        if object:
            return sorted(self.object2tag_map.get(object.pk,[]))


class SingletonObservableDetailView(BasicDetailView):

    template_name = 'mantis_actionables/%s/SingletonObservableDetails.html' % DINGOS_TEMPLATE_FAMILY

    model = SingletonObservable

    prefetch_related = ['type','subtype']

    title = "Indiator Details"



    stati_list = []

    sources_list = []

    def get_context_data(self, **kwargs):

        context = super(SingletonObservableDetailView, self).get_context_data(**kwargs)

        if self.stati_list:

            return self.stati_list
        else:


            self.stati_list = Status2X.objects.filter(object_id=self.kwargs['pk'],
                                                      content_type_id=CONTENT_TYPE_SINGLETON_OBSERVABLE).order_by("-timestamp")

            #self.stati_list = Status.objects.filter(
        context['stati2x'] = self.stati_list

        if self.sources_list:

            return self.sources_list
        else:

            self.sources_list = Source.objects.filter(object_id=self.kwargs['pk'],
                                                      content_type_id=CONTENT_TYPE_SINGLETON_OBSERVABLE).order_by("-timestamp").\
                prefetch_related('top_level_iobject_identifier__latest',
                                 'iobject_identifier__latest',
                                 'iobject_identifier__latest__iobject_type',
                                 'top_level_iobject_identifier__namespace',
                                 'import_info',
                                 'import_info__namespace'
                               )
        context['sources'] = self.sources_list


        return context




    @property
    def stati(self):
        logger.debug("Stati called")
        self.stati_list = Status.objects.filter(actionable_thru__object_id=self.kwargs['pk'],
                                                    actionable_thru__content_typeid=CONTENT_TYPE_SINGLETON_OBSERVABLE).order_by("-actionable_thru__timestamp")
        logger.debug("Done")
        return self.stati_list


class ImportInfoDetailsView(BasicFilterView):
    template_name = 'mantis_actionables/%s/ImportInfoDetails.html' % DINGOS_TEMPLATE_FAMILY

    filterset_class = SingletonObservablesFilter

    @property
    def object(self):
        return ImportInfo.objects.get(pk=self.kwargs.get('pk'))

    @property
    def queryset(self):
        return SingletonObservable.objects.filter(sources__import_info_id=self.kwargs.get('pk')).select_related('type','subtype')

    def title(self):

        return "%s" % self.object.name

    # TODO Pagination does not correctly here???
    paginate_by = 0

    object2tag_map = {}


    def object2tags(self,object):
        if not self.object2tag_map or not object:

            self.object2tag_map = {}
            tag_infos = self.object_list.values_list('pk','actionable_tags__actionable_tag__context__name',
                                                     'actionable_tags__actionable_tag__tag__name')
            for pk,context_name,tag_name in tag_infos:
                if True: #context_name == tag_name:
                    set_dict(self.object2tag_map,tag_name,'append',pk,context_name)


        if object:
            return self.object2tag_map.get(object.pk)



    def post(self, request, *args, **kwargs):
        self.form = InvestigationForm(request.POST.dict())
        form_valid = self.form.is_valid()
        cleaned_data = self.form.cleaned_data
        if form_valid:
            context_name = cleaned_data.get('investigation_tag')
            actionable_tag_bulk_action.delay(action="add",
                                             context_name_pairs=[(context_name,context_name)],
                                             thing_to_tag_pks= map(lambda x:x.pk,self.queryset),
                                             user=request.user,
                                             comment = "Investigation initiated on report '%s'" % self.object.name)
            ActionableTag.bulk_action(action="add",
                                      context_name_pairs=[(context_name,context_name)],
                                      thing_to_tag_pks= [self.object.pk],
                                      thing_to_tag_model= ImportInfo,
                                      user=request.user,
                                      comment = "Investigation initiated on report '%s'" % self.object.name)
            messages.success(request,"Investigation tag is being added to all indicators in this report.")
        else:
            messages.error(request,"Please chose a valid investigation tag.")
        return super(ImportInfoDetailsView, self).get(request, *args, **kwargs)


class ActionablesContextEditView(BasicDetailView):
    template_name = 'mantis_actionables/%s/ContextEdit.html' % DINGOS_TEMPLATE_FAMILY
    model = Context
    fields = ['title','description']

    form = None

    def get_context_data(self, **kwargs):

        context = super(ActionablesContextEditView, self).get_context_data(**kwargs)
        context['title'] = "Edit context: %s" % self.object.name

        if not self.form:
            self.form = ContextEditForm({'type': self.object.type,
                                         'title': self.object.title,
                                         'description': self.object.description,
                                         'related_incident_id' : self.object.related_incident_id},
                                         current_type = self.object.type,
                                         current_name = self.object.name)


        context['form'] = self.form

        return context


    #def get(self, request, *args, **kwargs):
    #    return super(ActionablesContextEditView, self).get(request, *args, **kwargs)


    def post(self, request, *args, **kwargs):
        super(ActionablesContextEditView,self).get(request, *args, **kwargs)
        self.form = ContextEditForm(request.POST.dict(),
                                    current_type = self.object.type,
                                    current_name = self.object.name)
        if self.form.is_valid():
            cleaned_data = self.form.cleaned_data
            type = int(cleaned_data['type'])

            self.object.title = cleaned_data['title']
            self.object.description = cleaned_data['description']
            self.object.related_incident_id = cleaned_data['related_incident_id']


            if type != self.object.type:


                # Rename dingos tag
                try:
                    tag = Tag.objects.get(name=self.object.name)
                except ObjectDoesNotExist:
                    tag = None

                if tag:
                    tag.name = cleaned_data['new_context_name']
                    tag.save()

                # Rename actionable tags

                TagName.objects.filter(name=self.object.name).update(name=cleaned_data['new_context_name'])
                self.object.name = cleaned_data['new_context_name']
                self.object.type = type
                messages.success(request,"Context and associated tags renamed to '%s'" % cleaned_data['new_context_name'])


            self.object.save()
            messages.success(request,"Changes written.")

            return HttpResponseRedirect(self.object.get_absolute_url())
        else:
            messages.error(request,"Please enter valid information.")


        return super(ActionablesContextEditView, self).get(request, *args, **kwargs)







    def get_object(self):
        return Context.objects.get(name=self.kwargs['context_name'])



