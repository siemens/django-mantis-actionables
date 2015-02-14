
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
import ipaddr
import re
import logging

from itertools import chain

from django.utils import timezone

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q

from dingos.models import InfoObject,Fact
from dingos.view_classes import POSTPROCESSOR_REGISTRY
from dingos.graph_traversal import follow_references

from . import ACTIVE_MANTIS_EXPORTERS, STIX_REPORT_FAMILY_AND_TYPES, SPECIAL_TAGS_REGEX
from .models import SingletonObservable, SingletonObservableType, SingletonObservableSubtype, Source, createStatus, Status, Status2X, Action, updateStatus,\
    Context, ActionableTag, ActionableTag2X, TagName, ActionableTaggingHistory

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




def update_and_transfer_tags(fact_pks,user=None):

    action = None

    # Extract all tags associated with the facts and populate
    # a mapping from fact pks to tags

    fact2tag_map = {}

    cols = ['id','tag_through__tag__name']
    tag_fact_q = list(Fact.objects.filter(id__in = fact_pks).filter(tag_through__isnull=False).values(*cols))

    for fact_tag_info in tag_fact_q:
        tag_list = fact2tag_map.setdefault(fact_tag_info['id'],[])
        tag_list.append(fact_tag_info['tag_through__tag__name'])


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

        found_tags = set(chain(*map(lambda x: fact2tag_map.get(x),fact_ids)))
        logger.debug("Found the following mantis tags: %s" % found_tags)

        # Extract the mantis tags that have been stored in mantis_actionables

        if singleton.mantis_tags:
            existing_tags = set(singleton.mantis_tags.split(','))
        else:
            existing_tags = set([])

        logger.debug("Recorded dingos tags in mantis_actionables: %s" % existing_tags)

        # calculate added and removed tags

        added_tags = found_tags.difference(existing_tags)

        logger.debug("Added dingos tags: %s" % added_tags)

        removed_tags = existing_tags.difference(found_tags)

        logger.debug("Removed dingos tags: %s" % removed_tags)


        if added_tags or removed_tags:

            # Tags have been added or removed -- possibly, we have to update the status
            updated_tag_info = list(found_tags)
            updated_tag_info.sort()

            updated_tag_info = ",".join(updated_tag_info)

            singleton.mantis_tags= updated_tag_info
            singleton.save()



            # We may have to update the status

            try:
                new_status = None
                status2x = Status2X.objects.get(content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                                                object_id=singleton.id,
                                                active=True)

                status = status2x.status
                new_status,created = updateStatus(status=status,
                                                  removed_tags = removed_tags,
                                                  added_tags = added_tags)

                logger.debug("Status %s created" % (status))


            except ObjectDoesNotExist:
                logger.critical("No status found for existing singleton observable. "
                                "I create one, but this should not happen!!!")
                status = createStatus(added_tags=added_tags,removed_tags=removed_tags)
                if not action:
                    action,action_created = Action.objects.get_or_create(user=user,comment="Tag addition or removal")
                status2x = Status2X(action=action,status=status,active=True,timestamp=timezone.now(),marked=singleton)
                status2x.save()
                created = False
            except MultipleObjectsReturned:
                logger.critical("Multiple active status2x objects returned: I take the most recent status2x object.")
                status2xes = Status2X.objects.filter(content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                                                     object_id=singleton.id,
                                                     active=True).order_by('-timestamp')
                status2X = status2xes[0]

                status2xes.update(active=False)

                status2X.active=True
                status2X.save()

                status = status2x.status
                new_status,created = updateStatus(status=status,
                                                  removed_tags = removed_tags,
                                                  added_tags = added_tags)


            if created or (new_status and new_status.id != status.id):
                logger.debug("Updating status")

                status2x.active = False
                status2x.save()
                if not action:
                    action,action_created = Action.objects.get_or_create(user=user,comment="Tag addition or removal")
                status2x_new = Status2X(action=action,status=new_status,active=True,timestamp=timezone.now(),marked=singleton)
                status2x_new.save()

        # Check if any tag is matching a specific pattern
        # TODO also treat removed tags
        for tag in added_tags:
            if any(regex.match(tag) for regex in SPECIAL_TAGS_REGEX):
                logger.debug("Found special tag %s" % tag)

                curr_context,created = Context.objects.get_or_create(name=tag)
                curr_tagname,created = TagName.objects.get_or_create(name=tag)
                curr_actionabletag,created = ActionableTag.objects.get_or_create(context=curr_context,
                                                                         tag=curr_tagname)
                curr_actionabletag2X,created = ActionableTag2X.objects.get_or_create(actionable_tag=curr_actionabletag,
                                                                             object_id=singleton.id,
                                                                             content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE)
                history,created = ActionableTaggingHistory.objects.get_or_create(tag=curr_actionabletag,
                                                                                 action=ActionableTaggingHistory.ADD,
                                                                                 object_id=singleton.id,
                                                                                 content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                                                                                 user=None)

            # We take the union as new tag info






def process_STIX_Reports(imported_since, imported_until=None):
    """
    Process all STIX reports that have been imported into MANTIS in a certain time slice.

    process_STIX_Reports carries out the following steps:

    - it performs a query that yields all STIX reports that have been imported
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

    - For each object yielded by the query for STIX reports, the fucntion carries
      out the imports specified in ACTIVE_MANTIS_EXPORTERS as specified in ``__init__.py``.
      The default setting is thus:

         ACTIVE_MANTIS_EXPORTERS = ['hashes','ips','fqdns']

      The  values in the list refer to the name specified in
      ``mantis_stix_importer.STIX_POSTPROCESSOR_REGISTRY``.

      Implementation hints for Philipp:

      - See the code in``dingos.views.InfoObjectExportsView`` for how to run an exporter.
      - Call the exporter with argument "override_columns = 'ALMOST_ALL'" to
        get complete information.

    - The function concatenates the results of all exporter runs. Here is an example
      single result of an IP export:

         {
          "category": "ipv4-addr",
          "object.import_timestamp": "2014-09-04 14:26:32.327645+00:00",
          "exporter": "IPs",
          "ip": "127.0.0.1",
          "object.name": "127.0.0.1 (1 facts)",
          "object.url": "/mantis/View/InfoObject/446977/",
          "object.object_family": "cybox.mitre.org",
          "object.identifier.namespace": "cert.test.siemens.com",
          "object.pk": "446977",
          "object.timestamp": "2014-09-04 14:26:32.254963+00:00",
          "apply_condition": "",
          "object.object_type.name": "AddressObject",
          "fact.pk": "225652",
          "value.pk": "123456",
          "object.identifier.uid": "Address-260a70ed-8f68-4de4-e760-61176b3ad20c-06368",
          "condition": ""
         }

    - The function extracts the set of all 'object.pk's. It then queries MANTIS for all
      facts in marking objects that are associated as markings with one of these objects
      and contain the fact_term with term 'Marking_Structure' and attribute '@color'
      and builds a dictionary mapping object-pks to TLP color (ignoring differences
      in lower/upper case)

    - For each export result, the function calls ``extract_singleton_observable`` to
      extract singleton observable type and value. It then does the following:

      - get or create the SingletonObservable object (please be smart about
        handling the SingletonObservableType: instead of querying for the pk
        again and again, use a global dictionary to store a mapping from
        type-name to pk and only look up types in the database
        that have not been encountered before

      - create a Source object and fills in
        - the links to the MANTIS-observables
        - TLP information
        - leave ORIGIN set to uncertain for now.

    """




    if not imported_until:
        imported_until = timezone.now()
    report_filters = []
    for report_filter in STIX_REPORT_FAMILY_AND_TYPES:
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



    # We leave the skip terms away since we are going in down direction,
    # so the danger that we pull in lot's of stuff we do not want
    # is lower

    #skip_terms = [{'term':'Related','operator':'icontains'}]

    skip_terms = []

    #tag_iobj_cache = {}

    # Mapping from fact ids to tags

    fact2tag_map = {}

    iobj2tlp_map = {}

    action = Action.objects.get_or_create(user=None,comment="Actionables Import")[0]

    for top_level_iobj in top_level_iobjs:
        graph= follow_references([top_level_iobj.id],
                                 skip_terms = skip_terms,
                                 direction='down'
                                 )
        postprocessor=None
        for exporter in ACTIVE_MANTIS_EXPORTERS:

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
                (content_type,results) = postprocessor.export(override_columns='EXPORTER', format='dict')

                if results:

                    # Find out the pks of all facts for which we still need to lookup the tag inforamation

                    fact_pks = set(map(lambda x: x.get('fact.pk'), results)) - set(fact2tag_map.keys())


                    #print "Affected Singletons"
                    #print affected_singletons



                    # Lookup the tagging info and add it to the mapping
                    cols = ['id','tag_through__tag__name']
                    tag_fact_q = list(Fact.objects.filter(id__in = fact_pks).filter(tag_through__isnull=False).values(*cols))
                    for fact_tag_info in tag_fact_q:
                        tag_list = fact2tag_map.setdefault(fact_tag_info['id'],[])
                        tag_list.append(fact_tag_info['tag_through__tag__name'])

                    # Find out the pks of all containing infoobjects for which we still need to lookup the
                    # marking TLP information

                    containing_iobj_pks = set(map(lambda x: x.get('object.pk'), results)) - set(iobj2tlp_map.keys())

                    select_columns = ['id','marking_thru__marking__fact_thru__fact__fact_values__value']
                    color_qs = InfoObject.objects.filter(id__in=containing_iobj_pks)\
                        .filter(marking_thru__marking__fact_thru__fact__fact_term__term='Marking_Structure', marking_thru__marking__fact_thru__fact__fact_term__attribute='color')\
                        .values_list(*select_columns)

                    for iobject_tlp_info in color_qs:
                        iobj2tlp_map[iobject_tlp_info[0]] = iobject_tlp_info[1].lower()


                    for result in results:

                        iobj_pk = int(result['object.pk'])
                        fact_pk = int(result['fact.pk'])
                        fact_value_pk = int(result['value.pk'])
                        type = result['actionable_type']
                        subtype = result['actionable_subtype']
                        if not subtype:
                            # If by mistake, subtype has been set to None,
                            # make sure that it is set to ''
                            subtype = ''
                        value = result['actionable_info']

                        if not (type and value):
                            continue
                        try:
                            type_pk = singleton_observable_types[type]
                        except KeyError:
                            obj, created = SingletonObservableType.objects.get_or_create(name=type)
                            singleton_observable_types[type] = obj.pk
                            type_pk = obj.pk


                        try:
                            subtype_pk = singleton_observable_subtypes[subtype]
                        except KeyError:
                            print "Subtype %s" % subtype
                            obj, created = SingletonObservableSubtype.objects.get_or_create(name=subtype)
                            singleton_observable_types[subtype] = obj.pk
                            subtype_pk = obj.pk


                        observable, created = SingletonObservable.objects.get_or_create(type_id=type_pk,subtype_id=subtype_pk,value=value)

                        source, created = Source.objects.get_or_create(iobject_id=iobj_pk,
                                                                    iobject_fact_id=fact_pk,
                                                                    iobject_factvalue_id=fact_value_pk,
                                                                    top_level_iobject=top_level_iobj,
                                                                    origin=Source.ORIGIN_UNCERTAIN,
                                                                    object_id=observable.id,
                                                                    content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE
                                                                    )

                        tlp_color = tlp_color_map.get(iobj2tlp_map.get(iobj_pk,None),Source.TLP_UNKOWN)
                        if not source.tlp == tlp_color:
                            source.tlp = tlp_color
                            source.save()

                        if created:
                            logger.info("Singleton Observable created (%s,%s,%s)" % (type,subtype,value))
                            new_status = createStatus(added_tags=[]) # TODO: pass source info
                            status2x = Status2X(action=action,status=new_status,active=True,timestamp=timezone.now(),marked=observable)
                            status2x.save()

                        else:
                            logger.debug("Singleton Observable (%s, %s, %s) not created, already in database" % (type,subtype,value))

                        # if False:
                        #
                        #     if observable.mantis_tags:
                        #         existing_tags = set(observable.mantis_tags.split(','))
                        #     else:
                        #         existing_tags = []
                        #
                        #     #update_and_transfer_tags(fact_pks=[fact_pk])
                        #
                        #     found_tags = set(fact2tag_map.get(fact_pk,[]))
                        #
                        #     added_tags = found_tags.difference(existing_tags)
                        #
                        #
                        #
                        #     # Check if any tag is matching a specific pattern
                        #     for tag in added_tags:
                        #         if any(regex.match(tag) for regex in SPECIAL_TAGS_REGEX):
                        #             logger.debug("Found special tag %s" % tag)
                        #
                        #             curr_context,created = Context.objects.get_or_create(name=tag)
                        #             curr_tagname,created = TagName.objects.get_or_create(name=tag)
                        #             curr_actionabletag,created = ActionableTag.objects.get_or_create(context=curr_context,
                        #                                                                      tag=curr_tagname)
                        #             curr_actionabletag2X,created = ActionableTag2X.objects.get_or_create(actionable_tag=curr_actionabletag,
                        #                                                                          object_id=observable.id,
                        #                                                                          content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE)
                        #             history,created = ActionableTaggingHistory.objects.get_or_create(tag=curr_actionabletag,
                        #                                                                              action=ActionableTaggingHistory.ADD,
                        #                                                                              object_id=observable.id,
                        #                                                                              content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                        #                                                                              user=None)
                        #
                        #
                        #     # We take the union as new tag info
                        #
                        #     updated_tag_info = list(found_tags.union(existing_tags))
                        #     updated_tag_info.sort()
                        #
                        #     updated_tag_info = ",".join(updated_tag_info)
                        #
                        #
                        #     observable.mantis_tags= updated_tag_info
                        #     observable.save()
                        #
                        #     if created:
                        #         logger.info("Singleton Observable created (%s,%s,%s)" % (type,subtype,value))
                        #         new_status = createStatus(added_tags=added_tags)
                        #         status2x = Status2X(action=action,status=new_status,active=True,timestamp=timezone.now(),marked=observable)
                        #         status2x.save()
                        #
                        #     else:
                        #         logger.debug("Singleton Observable (%s, %s, %s) not created, already in database" % (type,subtype,value))
                        #         new_status = None
                        #         try:
                        #             status2x = Status2X.objects.get(content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                        #                                             object_id=observable.id,
                        #                                             active=True)
                        #
                        #             status = status2x.status
                        #             new_status,created = updateStatus(status,
                        #                                               existing_tags = existing_tags,
                        #                                               added_tags = added_tags)
                        #
                        #             logger.debug("STATUS %s %s %s" % (status.id, new_status.id, created))
                        #         #TODO: multiple objects found?
                        #         except ObjectDoesNotExist:
                        #             status = createStatus(added_tags=added_tags)
                        #             status2x = Status2X(action=action,status=status,active=True,timestamp=timezone.now(),marked=observable)
                        #             status2x.save()
                        #             created = False
                        #         except MultipleObjectsReturned:
                        #             logger.critical("Multiple active status2x objects returned: I take the most recent status2x object.")
                        #             status2xes = Status2X.objects.filter(content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                        #                                                  object_id=observable.id,
                        #                                                  active=True).order_by('-timestamp')
                        #             status2X = status2xes[0]
                        #
                        #             status2xes.update(active=False)
                        #
                        #             status2X.active=True
                        #             status2X.save()
                        #
                        #             status = status2x.status
                        #             created = False
                        #
                        #
                        #         if created or (new_status and new_status.id != status.id):
                        #             logger.debug("Updating status")
                        #
                        #             status2x.active = False
                        #             status2x.save()
                        #
                        #             status2x_new = Status2X(action=action,status=new_status,active=True,timestamp=timezone.now(),marked=observable)
                        #             status2x_new.save()
                        #
                        #     source, created = Source.objects.get_or_create(iobject_id=iobj_pk,
                        #                                                 iobject_fact_id=fact_pk,
                        #                                                 iobject_factvalue_id=fact_value_pk,
                        #                                                 top_level_iobject=top_level_iobj,
                        #                                                 origin=Source.ORIGIN_UNCERTAIN,
                        #                                                 object_id=observable.id,
                        #                                                 content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE
                        #                                                 )
                        #
                        #     tlp_color = tlp_color_map.get(iobj2tlp_map.get(iobj_pk,None),Source.TLP_UNKOWN)
                        #     if not source.tlp == tlp_color:
                        #         source.tlp = tlp_color
                        #         source.save()

                    update_and_transfer_tags(fact2tag_map.keys())


