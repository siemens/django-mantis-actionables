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


import datetime
from querystring_parser import parser

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from dingos import DINGOS_TEMPLATE_FAMILY
from dingos.view_classes import BasicJSONView, BasicTemplateView, BasicFilterView, BasicUpdateView, BasicListView
from dingos.views import InfoObjectExportsView
from dingos.models import IdentifierNameSpace
from dingos.core.utilities import listify, set_dict
from dingos.templatetags.dingos_tags import show_TagDisplay

from . import DASHBOARD_CONTENTS
from .models import SingletonObservable,SingletonObservableType,Source,ActionableTag,TagName,ActionableTag2X,ActionableTaggingHistory,Context,Status
from .filter import ActionablesContextFilter, SingletonObservablesFilter, ImportInfoFilter
from .mantis_import import singleton_observable_types
from .tasks import async_export_to_actionables


#content_type_id
CONTENT_TYPE_SINGLETON_OBSERVABLE = ContentType.objects.get_for_model(SingletonObservable)

#init column_dict
COLS = {}

def fillColDict(colsDict,cols):
    for index,col in zip(range(len(cols)),cols):
        colsDict[index] = col

def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default

def datatable_query(table_name, post, paginate_at, **kwargs):
    post_dict = parser.parse(str(post.urlencode()))


    # Collect prepared statement parameters in here
    params = []

    table_spec = None

    try:
        table_spec = kwargs.pop('table_spec')
    except:
        pass

    if not table_spec:
        table_spec = DASHBOARD_CONTENTS[table_name]

    cols = kwargs.pop('cols')

    if not table_spec['show_type_column']:
        cols = cols['cut']
    else:
        cols = cols['all']

    cols = dict((x, y[0]) for x, y in cols.items())

    # Base query
    if table_spec['basis'] == 'SingletonObservable':
        base = SingletonObservable.objects
        types = table_spec['types']

        type_ids = []
        if isinstance(types,str):
            types = [types]
        for type in types:
            try:
                type_obj,created = SingletonObservableType.cached_objects.get_or_create(name=type)
                type_ids.append(type_obj.pk) #singleton_observable_types[type])
            except KeyError:
                continue
        q = base

        if type_ids:
            q = q.filter(type_id__in=type_ids)

        # extend query by kwargs['select_related']
        q = q.select_related(*kwargs.pop('select_related',[]))

        # extend query by kwargs['filter']
        for filter in kwargs.pop('filter',[]):
            q = q.filter(**filter)

        q = q.values_list(*(cols.values()))
        #sources__id for join on sources table
        q_count_all = q.count()


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



    q_count_filtered = q.count()
    # Treat the paging/limit
    length = safe_cast(post_dict.get('length'), int, paginate_at)
    if length<-1:
        length = paginate_at
    start = safe_cast(post_dict.get('start'), int, 0)
    if start<0:
        start = 0
    if length>0:
        q = q[start:start+length]
        params.append(length)
        params.append(start)


    return (q,q_count_all,q_count_filtered)


class BasicTableDataProvider(BasicJSONView):
    #add here filters and select_related statements to the base query
    filter = {}
    select_related = []

    table_spec = None

    table_rows = 10

    curr_cols = None
    def get_curr_cols(self):
        if self.curr_cols == None:
            self.init_data()
        return self.curr_cols

    @classmethod
    def init_data(cls):
        #should be provided to init the column dicts
        pass

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
        POST[u'length'] = "%s" % self.table_rows


        table_name = POST.get('table_type').replace(' ','_')

        kwargs =  {}
        if table_name in DASHBOARD_CONTENTS.keys():
            # Build the query for the data, and fetch that stuff
            kwargs = {
                'cols' : self.get_curr_cols(),
                'filter' : self.filter,
                'select_related' : self.select_related
            }
        elif self.table_spec:
             kwargs = {
                'cols' : self.get_curr_cols(),
                'filter' : self.filter,
                'select_related' : self.select_related
             }

        if kwargs:
             kwargs['table_spec'] = self.table_spec

             q,res['recordsTotal'],res['recordsFiltered'] = datatable_query(table_name, POST, paginate_at = self.table_rows, **kwargs)

             self.postprocess(table_name,res,q)
             return res

class SingletonObservablesWithSourceDataProvider(BasicTableDataProvider):

    select_related = ['sources__top_level_iobject_identifier__namespace',
                      'sources__top_level_iobject_identifier__latest' ]
    @classmethod
    def init_data(cls):
        cls.curr_cols = COLS.setdefault('standard',{})
        if not cls.curr_cols:
            #init default column_dicts
            cols_cut = cls.curr_cols.setdefault('cut',{})
            cols_all = cls.curr_cols.setdefault('all',{})

            #cols to display in tables (query_select_row,col_name,searchable)
            COLS_TO_DISPLAY = [
                ('sources__tlp','TLP','0'),
                ('sources__timestamp','Source TS','0'),
                ('value','Value','1'),
                ('sources__related_stix_entities__entity_type__name','Context Type','0'),
                ('sources__related_stix_entities__essence','Context Info','0'),
                ('sources__top_level_iobject_identifier__namespace__uri','Report Source','0'),
                ('sources__top_level_iobject_identifier__latest__name','Report Name','0'),

            ]

            #optinal columns to display (index,query_select_row,col_name,searchable)
            OPT_COLS = [
                (2,('subtype__name','Type','1')),]

            fillColDict(cols_cut,COLS_TO_DISPLAY)
            for index,content in OPT_COLS:
                COLS_TO_DISPLAY.insert(index,content)
            fillColDict(cols_all,COLS_TO_DISPLAY)

    def postprocess(self,table_name,res,q):
        for row in q:
            row = list(row)
            row[0] = Source.TLP_COLOR_CSS.get(row[0],'ERROR')
            #print row[1]
            #row[1] = datetime.datetime.date(row[1]).strftime('%Y-%m-%d %H:%M:%S %Z')
            #print "> %s" % row[1]
            res['data'].append(row)

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

class SingeltonObservablesWithSourceOneTableDataProvider(SingletonObservablesWithSourceDataProvider):
    table_spec =  {
        'basis': 'SingletonObservable',
        'name': 'All Imports',
        'types' : [],
        'show_type_column': True
    }

    # TODO only ten works at the moment -- there is some dependency on 10
    # in the calculation of the pagination
    table_rows = 10
    @classmethod
    def init_data(cls):
        cls.curr_cols = COLS.setdefault('all_imports',{})
        if not cls.curr_cols:
            #init default column_dicts
            cols_cut = cls.curr_cols.setdefault('cut',{})
            cols_all = cls.curr_cols.setdefault('all',{})

            #cols to display in tables (query_select_row,col_name,searchable)
            COLS_TO_DISPLAY = [
                ('sources__tlp','TLP','0'),
                ('sources__timestamp','Source TS','0'),
                ('type__name','Type','1'),
                ('subtype__name','Subtype','1'),
                ('value','Value','1'),
                ('sources__pk','Source PK','0'),
                ('sources__related_stix_entities__entity_type__name','Context Type','0'),
                ('sources__related_stix_entities__essence','Context Info','0'),
                ('sources__top_level_iobject_identifier__namespace__uri','Report Source','0'),
                ('sources__top_level_iobject_identifier__latest__name','Report Name','0'),

            ]


            #optinal columns to display (index,query_select_row,col_name,searchable)
            OPT_COLS = []

            fillColDict(cols_cut,COLS_TO_DISPLAY)
            for index,content in OPT_COLS:
                COLS_TO_DISPLAY.insert(index,content)
            fillColDict(cols_all,COLS_TO_DISPLAY)



class SingletonObservablesWithStatusDataProvider(BasicTableDataProvider):
    @classmethod
    def init_data(cls):
        cls.curr_cols = COLS.setdefault('status',{})
        if not cls.curr_cols:
            #init default column_dicts
            cols_cut = cls.curr_cols.setdefault('cut',{})
            cols_all = cls.curr_cols.setdefault('all',{})

            #cols to display in tables (query_select_row,col_name,searchable)
            COLS_TO_DISPLAY = [
                ('value','Value','1'),
                ('actionable_tags_cache','Tags','1')
            ]

            #optinal columns to display (index,query_select_row,col_name,searchable)
            OPT_COLS = [
                (1,('subtype__name','Type','1')),]

            fillColDict(cols_cut,COLS_TO_DISPLAY)
            for index,content in OPT_COLS:
                COLS_TO_DISPLAY.insert(index,content)
            fillColDict(cols_all,COLS_TO_DISPLAY)

    filter = [{
        'status_thru__active' : True
    }]
    #select_related = ['status_thru__status']

class SingletonObservablesWithStatusOneTableDataProvider(SingletonObservablesWithStatusDataProvider):
    table_spec =  {
    'basis': 'SingletonObservable',
    'name': 'Indicators and their status',
    'types' : [],
    'show_type_column': True
    }


    @classmethod
    def init_data(cls):
        cls.curr_cols = COLS.setdefault('all_status_infos',{})
        if not cls.curr_cols:
            #init default column_dicts
            cols_cut = cls.curr_cols.setdefault('cut',{})
            cols_all = cls.curr_cols.setdefault('all',{})

            #cols to display in tables (query_select_row,col_name,searchable)
            COLS_TO_DISPLAY = [
                ('status_thru__timestamp','Status Timestamp','0')  ,
                ('status_thru__status__most_permissive_tlp','lightest TLP','0')  ,
                ('status_thru__status__max_confidence','Max confidence','0'),
                ('status_thru__status__best_processing','Processing','0'),
                ('status_thru__status__kill_chain_phases','Kill Chain','0'),
                ('type__name','Type','1'),
                ('subtype__name','Subtype','1'),
                ('value','Value','1'),
                ('actionable_tags_cache','Tags','1')
            ]

            #optinal columns to display (index,query_select_row,col_name,searchable)
            OPT_COLS = []

            fillColDict(cols_cut,COLS_TO_DISPLAY)
            for index,content in OPT_COLS:
                COLS_TO_DISPLAY.insert(index,content)
            fillColDict(cols_all,COLS_TO_DISPLAY)

    def postprocess(self,table_name,res,q):
        for row in q:
            row = list(row)
            row[1] = Status.TLP_MAP[row[1]]
            row[2] = Status.CONFIDENCE_MAP[row[2]]
            row[3] = Status.PROCESSING_MAP[row[3]]

            res['data'].append(row)


    filter = [{
        'status_thru__active' : True
    }]
    #select_related = ['status_thru__status']


def all_status_infos(request):
    SingletonObservablesWithStatusOneTableDataProvider.init_data()
    name = 'all_status_infos'
    content_dict = {
        'title' : 'Indicators and their status',
        'tables' : [],
        'view' : name
    }


    content_dict['tables'].append((content_dict['title'],COLS[name]['all']))

    return render_to_response('mantis_actionables/%s/status.html' % DINGOS_TEMPLATE_FAMILY,
                              content_dict, context_instance=RequestContext(request))



def all_imports(request):
    SingeltonObservablesWithSourceOneTableDataProvider.init_data()
    name = 'all_imports'
    content_dict = {
        'title' : 'Indicators and their sources',
        'tables' : [],
        'view' : name
    }

    content_dict['tables'].append(('All',COLS[name]['all']))
    return render_to_response('mantis_actionables/%s/table_base.html' % DINGOS_TEMPLATE_FAMILY,
                              content_dict, context_instance=RequestContext(request))


def imports(request):
    SingletonObservablesWithSourceDataProvider.init_data()
    name = 'standard'
    content_dict = {
        'title' : 'Indicators and their sources',
        'tables' : [],
        'view' : name
    }

    for id,table_info in DASHBOARD_CONTENTS.items():
        if not table_info['show_type_column']:
            content_dict['tables'].append((table_info['name'],COLS[name]['cut']))
        else:
            content_dict['tables'].append((table_info['name'],COLS[name]['all']))
    return render_to_response('mantis_actionables/%s/table_base.html' % DINGOS_TEMPLATE_FAMILY,
                              content_dict, context_instance=RequestContext(request))

def status_infos(request):
    SingletonObservablesWithStatusDataProvider.init_data()
    name = 'status'
    content_dict = {
        'title' : 'Indicators and their status',
        'tables' : [],
        'view' : name
    }

    for id,table_info in DASHBOARD_CONTENTS.items():
        if not table_info['show_type_column']:
            content_dict['tables'].append((table_info['name'],COLS[name]['cut']))
        else:
            content_dict['tables'].append((table_info['name'],COLS[name]['all']))

    return render_to_response('mantis_actionables/%s/status.html' % DINGOS_TEMPLATE_FAMILY,
                              content_dict, context_instance=RequestContext(request))

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


    def object2tags(self,object):
        if not self.object2tag_map or not object:
            print "Calculating map"
            self.object2tag_map = {}
            tag_infos = self.object_list.values_list('pk','actionable_tags__actionable_tag__context__name',
                                                     'actionable_tags__actionable_tag__tag__name')
            for pk,context_name,tag_name in tag_infos:
                if context_name == self.curr_context_name:
                    set_dict(self.object2tag_map,tag_name,'append',pk)
            print self.object2tag_map

        if object:
            return sorted(self.object2tag_map.get(object.pk,[]))



    @property
    def queryset(self):
        tagged_object_pks = ActionableTag.objects.filter(context__name=self.curr_context_name)\
                                        .filter(actionable_tag_thru__singleton_observables__isnull=False)\
                                        .values_list('actionable_tag_thru__singleton_observables__id',flat=True)

        return SingletonObservable.objects.filter(pk__in=tagged_object_pks).select_related('type','subtype',
                                                                                           'actionable_tags__actionable_tag__context',
                                                                                           'actionable_tags__actionable_tag__tag').\
            prefetch_related('sources__top_level_iobject_identifier__latest','sources__top_level_iobject_identifier__namespace')



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


class ActionablesContextEditView(BasicUpdateView):
    template_name = 'mantis_actionables/%s/ContextEdit.html' % DINGOS_TEMPLATE_FAMILY
    model = Context
    fields = ['title','description']

    def get_context_data(self, **kwargs):

        context = super(ActionablesContextEditView, self).get_context_data(**kwargs)
        context['title'] = "Edit context: %s" % self.object.name
        return context

    def get_object(self):
        return Context.objects.get(name=self.kwargs['context_name'])

