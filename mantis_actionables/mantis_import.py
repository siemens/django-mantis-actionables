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

import logging

from json import dumps

from dingos.graph_utils import dfs_preorder_nodes

from datetime import timedelta

from itertools import chain

from django.utils import timezone

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q

from dingos.models import InfoObject,Fact,TaggingHistory
from dingos.view_classes import POSTPROCESSOR_REGISTRY
from dingos.graph_traversal import follow_references, annotate_graph

from . import MANTIS_ACTIONABLES_ACTIVE_EXPORTERS, MANTIS_ACTIONABLES_STIX_REPORT_FAMILY_AND_TYPES, MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX
from .models import SingletonObservable,\
    SingletonObservableType, \
    SingletonObservableSubtype, \
    Source, \
    Status2X, \
    Action, \
    ActionableTag, \
    STIX_Entity, \
    EntityType

from .status_management import updateStatus, createSourceMetaData

from tasks import async_export_to_actionables

logger = logging.getLogger(__name__)

#content_type_id
CONTENT_TYPE_SINGLETON_OBSERVABLE = ContentType.objects.get_for_model(SingletonObservable)

#build a name to pk mapping for SingletonObservableTypes on server startup
singleton_observable_types = {}
singleton_observable_types_qs = SingletonObservableType.objects.all()
for type in singleton_observable_types_qs:
    singleton_observable_types[type.name] = type.pk


#build a name to pk mapping for SingletonObservableTypes on server startup
singleton_observable_subtypes = {}
singleton_observable_subtypes_qs = SingletonObservableSubtype.objects.all()
for type in singleton_observable_subtypes_qs:
    singleton_observable_subtypes[type.name] = type.pk

#color tlp mapping
tlp_color_map = {}
for (id,color) in Source.TLP_KIND:
    tlp_color_map[color.lower()] = id



def determine_matching_dingos_tag_history_entry(action_flag,user,dingos_tag_name,fact_pks):
    """
    When importing changes in dingos-tags that lead to changes
    in the mantis_actionable tags, we want to provide an appropriate comment
    also in the history of the actionable tags.

    Problem: since the tag transfer may happen at any time and
    the set of dingos tags associated with a singleton observable
    is determined 'by bulk', we must try to find out the likely comment
    from the history of the dingos tags.

    We do this by filtering the dingos thag history for fitting dingos tag history items;
    if we find a likely item, we take the associated comment (and user, if this function was
    called without user information).
    """
    fact_content_type = ContentType.objects.get_for_model(Fact)
    just_now = timezone.now() - timedelta(milliseconds=2500)

    comment = ''

    result_user = None

    if user:
        # If a user has been provided to the function, the function has been
        # called during a tagging operation carried out by a user rather than
        # an import run: hence we look through history entries by that
        # particular user:

        likely_dingos_tag_history_entries = TaggingHistory.objects.filter(user=user,
                                                                          action = action_flag,
                                                                          tag__name = dingos_tag_name,
                                                                          object_id__in = fact_pks,
                                                                          content_type = fact_content_type).order_by('-timestamp')
    else:
        # otherwise, we just look for the most recent history entries concerning that particular
        # tag
        likely_dingos_tag_history_entries = TaggingHistory.objects.filter(action = action_flag,
                                                                          tag__name = dingos_tag_name,
                                                                          object_id__in = fact_pks,
                                                                          content_type = fact_content_type).order_by('-timestamp')
    result_user = None

    if likely_dingos_tag_history_entries:
        likely_matching_entry = likely_dingos_tag_history_entries[0]
        if user and likely_matching_entry.timestamp >= just_now:
            # If we find a tag history item due to the current user and
            # really really recent, we can be very sure that this is really
            # the history item that caused the tag change
            comment = likely_matching_entry.comment
        else:
            # Otherwise, we at least inform the reader that the comment
            # was derived
            if likely_matching_entry.comment:

                comment = "%s (Comment and user derived automatically from DINGOS tag)" % likely_matching_entry.comment
                result_user = likely_matching_entry.user
            else:
                comment = ""
        if (not result_user) and likely_matching_entry.user and likely_matching_entry.user != user:
            result_user = likely_matching_entry.user
            comment = "(User derived automatically from DINGOS tag history)"
        else:
            result_user = user

    return (result_user,comment)


def update_and_transfer_tag_action_to_dingos(action, context_name_set, affected_singleton_pks,user=None,comment=''):

    affected_singletons = SingletonObservable.objects.filter(id__in=affected_singleton_pks)

    affected_fact_ids = set(SingletonObservable.objects.filter(id__in=affected_singleton_pks).values_list('sources__iobject_fact',flat=True))
    #found_contexts = set(SingletonObservable.objects.all().values_list('actionable_tags__actionable_tag__context__name',flat=True))

    affected_facts = Fact.objects.filter(pk__in=affected_fact_ids)

    for affected_fact in affected_facts:
        existing_tags = set(affected_fact.tags.all())
        if action == 'add':
            changed_tags = context_name_set.difference(existing_tags)
            affected_fact.tags.add(*context_name_set)
        elif action == 'remove':
            changed_tags = existing_tags.difference(context_name_set)
            affected_fact.tags.remove(*context_name_set)

        TaggingHistory.bulk_create_tagging_history(action,changed_tags,[affected_fact],user,comment)

    for singleton in affected_singletons:
        if singleton.mantis_tags:
            existing_tags = set(singleton.mantis_tags.split(','))
        else:
            existing_tags = set([])
        if action == 'add':
            existing_tags.update(context_name_set)
        elif action == 'remove':
            existing_tags.difference_update(context_name_set)

        updated_tag_info = ",".join(existing_tags)

        singleton.mantis_tags= updated_tag_info
        singleton.save()





def update_and_transfer_tags(fact_pks,user=None):

    """
    Given a list or set of fact primary keys, the function does the following:

    - It gathers all the SingletonObjects that have a source in which a fact
      with one of the passed primary keys is referenced (upon import from MANTIS
      into mantis_actionables, each singleton observable that is detected during
      the import is linked with a source object that references the fact from
      which the singleton observable was derived)

    - For each of the singleton observables thus found, it does the following:

      - It calculates all dingos tags associated with each of the singleton objects
        by taking the union of all dingos tags associated with the facts referenced
        by sources of that particular singleton

      - It compares the set of dingos tags that has been stored with each singleton
        observable with the found of dingos tags that has now been found, thus
        finding out whether tags have been added or removed.

      - It stores the current set of dingos tags with the singleton observable.

      - If there has been a change in the set of tags, it calls a function
        that may update the status of the singleton observable.

      - It examines each added or removed tag and sees whether that has the
        form of an actionable context (actionable tags comprise a context
        and a name). If that is the case, it calls the actionable tag management
        function for the singleton observable with add/remove command and
        thus transfers the addition/removal of a context in dingos into
        mantis_actionables.

    """

    # In case a status change is carried out, an action object will
    # be created and referenced by the status change. During the
    # run of this function, we only create a single action object
    # which will then be associated with all status changes
    # due to this particular run of the function.

    action = None

    # Extract all tags associated with the facts and populate
    # a mapping from fact pks to dingos tags

    fact2tag_map = {}

    cols = ['id','tag_through__tag__name']
    tag_fact_q = list(Fact.objects.filter(id__in = fact_pks).filter(tag_through__isnull=False).values(*cols))

    for fact_tag_info in tag_fact_q:
        tag_list = fact2tag_map.setdefault(fact_tag_info['id'],[])
        tag_list.append(fact_tag_info['tag_through__tag__name'])

    logger.debug("Calculated fact2tag_map as %s" % fact2tag_map)

    # Find out all singleton observables in the mantis_actionables app that
    # have a link to one of the facts via a source object

    affected_singletons = SingletonObservable.objects.filter(sources__iobject_fact__in=fact_pks).prefetch_related('sources')

    # Update tag information in mantis_actionables for each of these
    # singleton observables

    for singleton in affected_singletons:
        logger.debug("Treating singleton observable %s" % singleton)
        # Determine the facts associated with this singleton
        fact_ids = set(map(lambda x: x.iobject_fact_id, singleton.sources.all()))

        # Use the fact2tag_map to determine all mantis tags associated with the
        # singleton

        logger.debug("Found the following fact ids: %s" % fact_ids)

        found_tags = set(chain(*map(lambda x: fact2tag_map.get(x,[]),fact_ids)))

        logger.debug("Found the following mantis tags: %s" % found_tags)

        # Extract the mantis tags that have been stored in mantis_actionables

        if singleton.mantis_tags:
            existing_tags = set(singleton.mantis_tags.split(','))
        else:
            existing_tags = set([])

        logger.debug("Hitherto recorded dingos tags in mantis_actionables: %s" % existing_tags)

        # calculate added and removed tags

        added_tags = found_tags.difference(existing_tags)

        logger.debug("Added dingos tags: %s" % added_tags)

        removed_tags = existing_tags.difference(found_tags)

        logger.debug("Removed dingos tags: %s" % removed_tags)


        if added_tags or removed_tags:

            # Tags have been added or removed: we store the current list
            # of dingos tags with the singleton observable.

            updated_tag_info = list(found_tags)
            updated_tag_info.sort()

            updated_tag_info = ",".join(updated_tag_info)

            singleton.mantis_tags= updated_tag_info
            singleton.save()

            # We may have to update the status

            singleton.update_status(update_function=updateStatus,
                                    action=action,
                                    user=user,
                                    added_tags=added_tags,
                                    removed_tags=removed_tags)

        # Check if any of the added/removed dingos tag is matching the context pattern.
        # If it is, transfer the change into the set of actionable tags associated with
        # this singleton observable

        if added_tags or removed_tags:

            for tag in added_tags:
                if any(regex.match(tag) for regex in MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX):
                    logger.debug("Found added special tag %s" % tag)
                    (result_user,comment) = determine_matching_dingos_tag_history_entry(TaggingHistory.ADD,
                                                                                        user,
                                                                                        tag,
                                                                                        fact_ids)
                    ActionableTag.bulk_action(action = 'add',
                                              context_name_pairs=[(tag,tag)],
                                              thing_to_tag_pks=[singleton.pk],
                                              user=result_user,
                                              comment=comment,
                                              supress_transfer_to_dingos=True)
            for tag in removed_tags:
                if any(regex.match(tag) for regex in MANTIS_ACTIONABLES_CONTEXT_TAG_REGEX):
                    logger.debug("Found special tag %s" % tag)
                    (result_user,comment) = determine_matching_dingos_tag_history_entry(TaggingHistory.REMOVE,
                                                                                        user,
                                                                                        tag,
                                                                                        fact_ids)
                    ActionableTag.bulk_action(action = 'remove',
                                              context_name_pairs=[(tag,tag)],
                                              thing_to_tag_pks=[singleton.pk],
                                              user=result_user,
                                              comment=comment,
                                              supress_transfer_to_dingos=True)



def import_singleton_observables_from_STIX_iobjects(top_level_iobjs, user = None):
    """
    The function carries out the following actions:

    - For each object passed to the function, it determines the
      downward reachability graph and then carries out the
      the imports specified in ACTIVE_MANTIS_EXPORTERS as specified in ``__init__.py``
      on these graphs.

      The default setting for the called importers is thus:

         ACTIVE_MANTIS_EXPORTERS = ['cybox_all']

      The  values in the list refer to the name specified in
      ``mantis_stix_importer.STIX_POSTPROCESSOR_REGISTRY``.

    - The function concatenates the results of all exporter runs. In order to
      be imported into mantis_actionables, a single exporter result must
      yield the following keys::

    """

    # We leave the skip terms away since we are going in down direction,
    # so the danger that we pull in lot's of stuff we do not want
    # is lower

    #skip_terms = [{'term':'Related','operator':'icontains'}]

    skip_terms = []


    if top_level_iobjs:
        if isinstance(top_level_iobjs[0],InfoObject):
            top_level_iobj_pks = map(lambda x:x.pk, top_level_iobjs)
        else:
            top_level_iobj_pks = top_level_iobjs


    action, created_action = Action.objects.get_or_create(user=user,comment="Actionables Import")

    results_per_top_level_obj = []

    for top_level_iobj_pk in top_level_iobj_pks:
        graph= follow_references([top_level_iobj_pk],
                                 skip_terms = skip_terms,
                                 direction='down'
                                 )
        top_level_iobj_identifier_pk = graph.node[top_level_iobj_pk]['identifier_pk']


        postprocessor=None

        results = []

        for exporter in MANTIS_ACTIONABLES_ACTIVE_EXPORTERS:

            postprocessor_classes = POSTPROCESSOR_REGISTRY[exporter]

            for postprocessor_class in postprocessor_classes:

                postprocessor = postprocessor_class(graph=graph,
                                                    query_mode='vIO2FValue',
                                                    # By feeding in the existing postprocessor,
                                                    # we re-use the information that has
                                                    # already been pulled from the database
                                                    # rather than pulling it again for
                                                    # each iteration.
                                                    details_obj = postprocessor
                                                    )
                (content_type,part_results) = postprocessor.export(override_columns='EXPORTER', format='exporter')

                results += part_results


        if results:
            results_per_top_level_obj.append((top_level_iobj_pk,results))

    for (top_level_iobj_pk, results) in results_per_top_level_obj:
        #async_export_to_actionables(top_level_iobj_pk,results,action=action)

        import_singleton_observables_from_export_result(top_level_iobj_identifier_pk,top_level_iobj_pk,results,action=action,user=user,graph=graph)

def import_singleton_observables_from_export_result(top_level_iobj_identifier_pk,top_level_iobj_pk,results,action=None,user=None,graph=None):
    """
    The function takes the primary key of an InfoObject representing a top-level STIX object
    and a list of results that have the following shape::

        {

         (...)

         "actionable_type": <e.g., 'Hash'>
         "actionable_subtype": <e.g., 'MD5', can be empty for other types>
         "actionable_info": <basic information, e.g., hash value>

         (...)

         "object.pk": <pk of information object in which fact was found from
                       which the actionable info has been derived>
         "fact.pk": <pk of fact from which actionable info was derived>
         "value.pk": <pk of value from which actionable info was derived>

        },

    - The function extracts the set of all 'object.pk's. It then queries MANTIS for all
      facts in marking objects that are associated as markings with one of these objects
      and contain the fact_term with term 'Marking_Structure' and attribute '@color'
      and builds a dictionary mapping object-pks to TLP color (ignoring differences
      in lower/upper case)

    - It then does the following:

      - get or create the SingletonObservable object

      - create a Source object and fills in
        - the links to the MANTIS-observables
        - TLP information
        - leave ORIGIN set to uncertain for now.

      - transfer tags from dingos into actionables
      - create or update the status of the singleton observable

    """

    # Mapping from fact ids to tags

    fact2tag_map = {}

    # Mapping information objects to TLP information

    iobj2tlp_map = {}

    # Mapping from identifier_pks to related_entities

    identifier_pk_2_related_entity_map = {}

    if not action:
        action, created_action = Action.objects.get_or_create(user=user,comment="Actionables Import")


    containing_iobj_pks = set(map(lambda x: x.get('_iobject_pk'), results))

    select_columns = ['identifier_id','marking_thru__marking__fact_thru__fact__fact_values__value']
    color_qs = InfoObject.objects.filter(id__in=containing_iobj_pks)\
        .filter(marking_thru__marking__fact_thru__fact__fact_term__term='Marking_Structure',
                marking_thru__marking__fact_thru__fact__fact_term__attribute='color')\
        .values_list(*select_columns)

    for iobject_tlp_info in color_qs:
        iobj2tlp_map[iobject_tlp_info[0]] = iobject_tlp_info[1].lower()

    for result in results:

        identifier_pk = int(result['_identifier_pk'])
        iobject_pk = int(result['_iobject_pk'])
        fact_pk = int(result['_fact_pk'])
        fact_value_pk = int(result['_value_pk'])
        type = result.get('actionable_type','')
        subtype = result.get('actionable_subtype','')

        if not subtype:
            # If by mistake, subtype has been set to None,
            # make sure that it is set to ''
            subtype = ''

        value = result.get('actionable_info','')

        if not (type and value):
            logger.error("Incomplete actionable information %s/%s for value %s" % (type,subtype,value))
            continue

        src_meta_data = createSourceMetaData(top_level_node=graph.node[top_level_iobj_pk])
        if not src_meta_data:
            src_meta_data = {}

        origin_info = src_meta_data.get('origin',Source.ORIGIN_UNKNOWN)
        processing_info = src_meta_data.get('processing',Source.PROCESSING_UNKNOWN)




        singleton_type_obj = SingletonObservableType.cached_objects.get_or_create(name=type)[0]
        singleton_subtype_obj = SingletonObservableSubtype.cached_objects.get_or_create(name=subtype)[0]

        observable, observable_created = SingletonObservable.objects.get_or_create(type=singleton_type_obj,
                                                                                   subtype=singleton_subtype_obj,
                                                                        value=value)

        source, source_created = Source.objects.get_or_create(iobject_identifier_id=identifier_pk,

                                                       iobject_fact_id=fact_pk,
                                                       iobject_factvalue_id=fact_value_pk,
                                                       top_level_iobject_identifier_id=top_level_iobj_identifier_pk,
                                                       object_id=observable.id,
                                                       content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                                                       defaults = {
                                                          'iobject_id': iobject_pk,
                                                          'top_level_iobject_id' : top_level_iobj_pk,
                                                          'processing': processing_info,
                                                          'origin': origin_info
                                                       }

                                                    )
        if not source_created:
            logger.debug("Found existing source object, updating")
            source.iobject_id = iobject_pk
            source.top_level_iobject_id = top_level_iobj_pk
            source.processing = processing_info
            source.origin = origin_info
        else:
            logger.debug("Created new source object")


        entities=[]

        if not graph:
            print "NO GRAPH PASSED!!!"
            related_iobject_pks = map (lambda x: x['iobject_pk'], result['_relationship_info'])
            graph = follow_references(related_iobject_pks,
                                      skip_terms = [],
                                      direction='down'
                                      )

            annotate_graph(graph)

        for node in result['_relationship_info']:
            essence_info = extract_essence(node, graph)

            if not essence_info:
                essence_info = None
            else:
                essence_info = dumps(essence_info)

            if essence_info:
                node_identifier_pk = node['identifier_pk']


                entity = identifier_pk_2_related_entity_map.get(node_identifier_pk)

                if not entity:
                    entity_type, created = EntityType.cached_objects.get_or_create(name=node['iobject_type'])
                    entity, created = STIX_Entity.objects.get_or_create(iobject_identifier_id=node_identifier_pk,
                                                                        non_iobject_identifier='',
                                                                        defaults={'essence': essence_info,
                                                                                  'entity_type':entity_type})
                    if not created:
                        entity.essence = essence_info
                        entity.entity_type = entity_type
                        entity.save()

                    identifier_pk_2_related_entity_map[node_identifier_pk] = entity


                entities.append(entity)


        source.related_stix_entities.clear()

        source.related_stix_entities.add(*entities)

        print iobj2tlp_map


        tlp_color = tlp_color_map.get(iobj2tlp_map.get(identifier_pk,None),Source.TLP_UNKOWN)
        if not source.tlp == tlp_color:
            source.tlp = tlp_color
            source.save()

        if observable_created:
            logger.info("Singleton Observable created (%s,%s,%s)" % (type,subtype,value))

        else:
            logger.info("Existing Singleton Observable (%s,%s,%s) found" % (type,subtype,value))
        observable.update_status(update_function=updateStatus,
                                 action=action,
                                 user=user,
                                 source_obj = source,
                                 related_entities = entities)

    fact_pks = set(map(lambda x: x.get('fact.pk'), results))
    update_and_transfer_tags(fact_pks,user=user)


def process_STIX_Reports(imported_since, imported_until=None):
    """
    Process all STIX reports that have been imported into MANTIS in a certain time slice:

    - It performs a query that yields all STIX reports that have been imported
      since the date-time provided by the parameter ``imported_since`` and no later
      than the date-time provided by the parameter ``imported_until`` (if no
      such date has been provided, then all reports up to the present time are taken.

      What consitutes a STIX report is configurable via the setting

      STIX_REPORT_FAMILY_AND_TYPES specified in ``__init__.py``. The default
      setting is thus::

         STIX_REPORT_FAMILY_AND_TYPES = [{'iobject_type': 'STIX_Package',
                                          'iobject_type_family': 'stix.mitre.org'}]

      (Once STIX 1.2 is released, we may have to add STIX_Report here and probably
      add some intelligence to disregard packages if they contain a report object...)

    - Call the import function on the determined STIX reports

    """
    if not imported_until:
        imported_until = timezone.now()
    report_filters = []
    for report_filter in MANTIS_ACTIONABLES_STIX_REPORT_FAMILY_AND_TYPES:
        report_filters.append({
            'iobject_type__name' : report_filter['iobject_type'],
            'iobject_family__name' : report_filter['iobject_type_family']
        })
    queries = [Q(**filter) for filter in report_filters]
    query = queries.pop()

    # Or the Q object with the ones remaining in the list
    for item in queries:
        query |= item
    top_level_iobjs = InfoObject.objects.filter(create_timestamp__gte=imported_since,
                                                create_timestamp__lte=imported_until)
    top_level_iobjs = list(top_level_iobjs.filter(query))
    return import_singleton_observables_from_STIX_iobjects(top_level_iobjs)

def extract_essence(node_info, graph):
    result = {}
    if node_info['iobject_type'] == 'Indicator':
        confidence_facts = [ x.value for x in node_info['facts'] if x.term == 'Confidence/Value']

        if confidence_facts:

            result['confidence'] = confidence_facts[0]

        kill_chain_phase_object_pks = list(dfs_preorder_nodes(graph,
                                           source=node_info['iobject'].pk,
                                           edge_pred= lambda x : 'phase_id' in x['attribute']))[1:]
        kill_chain_phase_nodes = map(lambda x: graph.node[x],kill_chain_phase_object_pks)
        print kill_chain_phase_nodes

        for kill_chain_phase_node in kill_chain_phase_nodes:
            kill_chain_phase_names = [ x.value for x in kill_chain_phase_node['facts'] if x.attribute == 'name']
            if kill_chain_phase_names:
                kill_chain_phases = result.setdefault('kill_chain_phases',set([]))
                kill_chain_phases.update(kill_chain_phase_names)

        if 'kill_chain_phases' in result:
            result['kill_chain_phases'] = list(result['kill_chain_phases'])
            result['kill_chain_phases'].sort()
            result['kill_chain_phases'] = ';'.join(result['kill_chain_phases'])

    elif node_info['iobject_type'] == "ThreatActor":
        identity_object_pks = list(dfs_preorder_nodes(graph,
                              source=node_info['iobject'].pk,
                              edge_pred= lambda x : 'Identity' in x['term']))[1:]

        identity_object_nodes = map(lambda x: graph.node[x],identity_object_pks)
        #print identity_object_nodes
        for identity_object_node in identity_object_nodes:
            identity_names = [x.value for x in identity_object_node['facts'] if x.term == 'Name' and x.attribute == '']
            if identity_names:
                identities = result.setdefault('identities',set([]))
                identities.update(identity_names)

        if 'identities' in result:
            result['identities'] = list(result['identities'])
            result['identities'].sort()
            result['identities'] = ';'.join(result['identities'])

    elif node_info['iobject_type'] == "Campaign":
        identity_names = [ x.value for x in node_info['facts'] if x.term == 'Names/Name' and x.attribute == '']
        if identity_names:
            identities = result.setdefault('names',set([]))
            identities.update(identity_names)
        if 'names' in result:
            result['names'] = list(result['names'])
            result['names'].sort()
            result['names'] = ';'.join(result['names'])





    return result



