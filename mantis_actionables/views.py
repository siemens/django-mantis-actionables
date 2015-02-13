
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
from dingos.view_classes import BasicJSONView, BasicTemplateView
from dingos.models import IdentifierNameSpace
from dingos.core.utilities import listify
from dingos.templatetags.dingos_tags import show_TagDisplay

from . import DASHBOARD_CONTENTS
from .models import SingletonObservable,Source,ActionableTag,TagName,ActionableTag2X,ActionableTaggingHistory,Context
from .mantis_import import singleton_observable_types

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

def datatable_query(table_name, post, **kwargs):
    post_dict = parser.parse(str(post.urlencode()))

    # Collect prepared statement parameters in here
    params = []

    table = DASHBOARD_CONTENTS[table_name]

    cols = kwargs.pop('cols')
    if not table['show_type_column']:
        cols = cols['cut']
    else:
        cols = cols['all']

    cols = dict((x, y[0]) for x, y in cols.items())

    # Base query
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
            q = base

            # extend query by kwargs['select_related']
            q = q.select_related(*kwargs.pop('select_related',[]))

            # extend query by kwargs['filter']
            for filter in kwargs.pop('filter',[]):
                q = q.filter(**filter)

            q = q.filter(type_id__in=type_ids).values_list(*(cols.values()))
            #sources__id for join on sources table
            q_count_all = q.count()

        else:
            return (base.none(),0,0)


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

    return (q,q_count_all,q_count_filtered)


class ActionablesBaseTableSource(BasicJSONView):
    #add here filters and select_related statements to the base query
    filter = {}
    select_related = []

    @classmethod
    def init_data(cls):
        #should be provided to init the column dicts
        pass

    def postprocess(self,table_name,res,q):
        #insert fetched rows into result
        for row in q:
            res['data'].append(row)

        #treat filters
        if res['draw'] == 1:
            res['cols'][table_name + '_type_filter'] = [{'all': 'All'}]
            types = DASHBOARD_CONTENTS[table_name]['types']
            if len(types) > 1:
                for type_name in types :
                    res['cols'][table_name + '_type_filter'].append({type_name: type_name})

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
        POST[u'length'] = u'10'

        table_name = POST.get('table_type')
        if table_name in DASHBOARD_CONTENTS.keys():
            # Build the query for the data, and fetch that stuff
            kwargs = {
                'cols' : self.curr_cols,
                'filter' : self.filter,
                'select_related' : self.select_related
            }

            q,res['recordsTotal'],res['recordsFiltered'] = datatable_query(table_name, POST, **kwargs)

            self.postprocess(table_name,res,q)
        return res


class ActionablesTableStandardSource(ActionablesBaseTableSource):
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
                ('sources__top_level_iobject__identifier__namespace__uri','STIX Namespace','0'),
                ('sources__top_level_iobject__name','STIX Name','0')
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
            row[0] = Source.TLP_COLOR_CSS[row[0]]
            row[1] = datetime.datetime.date(row[1]).strftime('%d-%m-%Y %X')
            res['data'].append(row)

        #treat filters
        if res['draw'] == 1:
            res['cols'][table_name + '_type_filter'] = [{'all': 'All'}]
            types = DASHBOARD_CONTENTS[table_name]['types']
            if len(types) > 1:
                for type_name in types :
                    res['cols'][table_name + '_type_filter'].append({type_name: type_name})
            res['cols'][table_name + '_tlp_filter'] = [{'all': 'All'}]
            res['cols'][table_name + '_ns_filter'] = [{'all' : 'All'}]
            namespaces = list(IdentifierNameSpace.objects.all().values_list('uri',flat=True))
            if len(namespaces) > 1:
                for ns in namespaces:
                    res['cols'][table_name + '_ns_filter'].append({ns : ns})


class ActionablesTableStatusSource(ActionablesBaseTableSource):
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
                ('mantis_tags','Tags','1')
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
    select_related = ['status_thru__status']


def imports(request):
    ActionablesTableStandardSource.init_data()
    name = 'standard'
    content_dict = {
        'title' : 'Actionables',
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
    ActionablesTableStatusSource.init_data()
    name = 'status'
    content_dict = {
        'title' : 'Imported Observables - Status View',
        'tables' : [],
        'view' : name
    }

    for id,table_info in DASHBOARD_CONTENTS.items():
        if not table_info['show_type_column']:
            content_dict['tables'].append((table_info['name'],COLS[name]['cut']))
        else:
            content_dict['tables'].append((table_info['name'],COLS[name]['all']))
    print content_dict
    return render_to_response('mantis_actionables/%s/status.html' % DINGOS_TEMPLATE_FAMILY,
                              content_dict, context_instance=RequestContext(request))

def processActionablesTagging(data,**kwargs):
    action = data['action']
    obj_pks = data['objects']
    tags = listify(data['tags'])
    print "Passed tags %s" % tags

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
            tag_name_obj = []
            context,created = Context.objects.get_or_create(name=curr_context)
            if action == 'add':
                for tag in tags:
                    curr_tag, created = TagName.objects.get_or_create(name=tag)
                    actionable_tag,created = ActionableTag.objects.get_or_create(context=context,
                                                                         tag=curr_tag)
                    tag_name_obj.append(actionable_tag)
                    for pk in obj_pks:
                        actionable_tag_2x,created = ActionableTag2X.objects.get_or_create(actionable_tag=actionable_tag,
                                                                          object_id=pk,
                                                                          content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE)

                curr_context = show_TagDisplay([tag],'actionables',isEditable=True)
                tag_html = render_to_string('dingos/%s/includes/_TagDisplay.html' % (DINGOS_TEMPLATE_FAMILY),curr_context)
                res['html'] = tag_html
                res['status'] = 0
                comment = '' if not user_data else user_data
                ActionableTaggingHistory.bulk_create_tagging_history(action,tag_name_obj,obj_pks,user,comment)

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
                        for tag in tags:
                            curr_tag = TagName.objects.get(name=tag)
                            actionable_tag = ActionableTag.objects.get(context=context,
                                                               tag=curr_tag)
                            tag_name_obj.append(actionable_tag)
                            for pk in obj_pks:
                                ActionableTag2X.objects.get(actionable_tag=actionable_tag,
                                                    object_id=pk,
                                                    content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE).delete()
                        ActionableTaggingHistory.bulk_create_tagging_history(action,tag_name_obj,obj_pks,user,user_data)
                        res['status'] = 0
        else:
            res['err'] = 'no tag provided'
            res['status'] = -1
    else:
        raise NotImplementedError('%s not a possible action to perform') % (action)

    return res


class ActionablesContextView(BasicTemplateView):
    template_name = 'mantis_actionables/%s/ContextView.html' % DINGOS_TEMPLATE_FAMILY

    title = 'Context View'

    order_by_dict = {'type':'actionable_tag_thru__singleton_observables__type__name',
                     'subtype':'actionable_tag_thru__singleton_observables__subtype__name',
                     'value': 'actionable_tag_thru__singleton_observables__value'}



    def get_context_data(self, **kwargs):


        context = super(ActionablesContextView, self).get_context_data(**kwargs)

        # TODO: Below, the tagged singleton observables are extracted
        # via the Actionable tag. It would be more natural to
        # query via SingletonObservable and aggregate the tags...

        cols = ['tag__name',\
                'actionable_tag_thru__singleton_observables__type__name',\
                'actionable_tag_thru__singleton_observables__subtype__name',\
                'actionable_tag_thru__singleton_observables__value',\
                'actionable_tag_thru__singleton_observables__id']
        matching_observables = ActionableTag.objects.filter(context__name=self.curr_context_name)\
                                        .filter(actionable_tag_thru__singleton_observables__isnull=False)\
                                        .values_list(*cols)

        action_tags = ActionableTag.objects.filter(context__name=self.curr_context_name)

        # TODO: This does not work because the order is thrown away below when
        # aggregating the tags.

        if self.order_by:
            matching_observables.order_by(self.order_by)


        obs_tag_map = {}
        for observable in matching_observables:
            obs = obs_tag_map.setdefault((observable[1],observable[2],observable[3],observable[4]),[])
            obs.append(observable[0])


        context['isEditable'] = True
        context['obs_tag_map'] = obs_tag_map
        return context

    def get(self,request, *args, **kwargs):
        self.order_by = self.order_by_dict.get(request.GET.get('o'))
        self.curr_context_name = kwargs.get('context_name')
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
                         filter(tag__context__name=self.tag_context).order_by('timestamp').\
                         values(*cols_history))

        obj_info_mapping = {}
        for model,cols in self.possible_models.items():
            content_id = ContentType.objects.get_for_model(model).id
            setattr(self,'pks',set([x['object_id'] for x in history_q if x['content_type_id'] == content_id]))
            model_q = model.objects.filter(id__in=self.pks).values(*cols)
            current_model_map = obj_info_mapping.setdefault(content_id,{})
            for obj in model_q:
                print obj
                current_model_map[obj['id']] = obj
            del self.pks
        context['mode'] = self.mode
        context['tag_context'] = self.tag_context
        context['history'] = history_q
        context['map_objs'] = obj_info_mapping
        context['map_action'] = ActionableTaggingHistory.ACTIONS
        return context

    def get(self, request, *args, **kwargs):
        self.mode = request.GET.get('mode')

        self.tag_context = kwargs.pop('tag_context',None)
        self.title = "Timeline for '%s'" % self.tag_context
        return super(ActionablesTagHistoryView,self).get(request, *args, **kwargs)
