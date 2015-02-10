
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

#content_type_id
CONTENT_TYPE_SINGLETON_OBSERVABLE = ContentType.objects.get_for_model(SingletonObservable)


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
                    print map(lambda x: x.get('fact.pk'), results)
                    fact_pks = set(map(lambda x: x.get('fact.pk'), results)) - set(fact2tag_map.keys())
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
                        value = result['actionable_info']

                        if not (type and value):
                            continue
                        try:
                            type_pk = singleton_observable_types[type]
                        except KeyError:
                            obj, created = SingletonObservableType.objects.get_or_create(name=type)
                            singleton_observable_types[type] = obj.pk
                            type_pk = obj.pk

                        if subtype:
                            try:
                                subtype_pk = singleton_observable_subtypes[subtype]
                            except KeyError:
                                obj, created = SingletonObservableSubtype.objects.get_or_create(name=subtype)
                                singleton_observable_types[subtype] = obj.pk
                                subtype_pk = obj.pk

                        if subtype:
                            observable, created = SingletonObservable.objects.get_or_create(type_id=type_pk,subtype_id=subtype_pk,value=value)
                        else:
                            observable, created = SingletonObservable.objects.get_or_create(type_id=type_pk,value=value)

                        if observable.mantis_tags:
                            existing_tags = set(observable.mantis_tags.split(','))
                        else:
                            existing_tags = []

                        found_tags = set(fact2tag_map.get(fact_pk,[]))

                        added_tags = found_tags.difference(existing_tags)

                        # Check if any tag is matching a specific pattern
                        for tag in added_tags:
                            if any(regex.match(tag) for regex in SPECIAL_TAGS_REGEX):
                                curr_context,created = Context.objects.get_or_create(name=tag)
                                curr_tagname,created = TagName.objects.get_or_create(name=tag)
                                curr_actionabletag,created = ActionableTag.objects.get_or_create(context=curr_context,
                                                                                         tag=curr_tagname)
                                curr_actionabletag2X,created = ActionableTag2X.objects.get_or_create(actionable_tag=curr_actionabletag,
                                                                                             object_id=observable.id,
                                                                                             content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE)
                                history,created = ActionableTaggingHistory.objects.get_or_create(tag=curr_actionabletag,
                                                                                                 action=ActionableTaggingHistory.ADD,
                                                                                                 object_id=observable.id,
                                                                                                 content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,
                                                                                                 user=None)


                        # We take the union as new tag info

                        updated_tag_info = list(found_tags.union(existing_tags))
                        updated_tag_info.sort()

                        updated_tag_info = ",".join(updated_tag_info)

                        #print "Updated %s" % updated_tag_info
                        #print "Added %s" % added_tags
                        #print "Found %s" % found_tags

                        observable.mantis_tags= updated_tag_info
                        observable.save()

                        if created:
                            print "singleton created (%s,%s)" % (type,value)
                            new_status = createStatus(added_tags=added_tags)
                            status2x = Status2X(action=action,status=new_status,active=True,timestamp=timezone.now(),marked=observable)
                            status2x.save()

                        else:
                            print "singleton (%s, %s) not created, already in database" % (type,value)
                            new_status = None
                            try:
                                status2x = Status2X.objects.get(content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,object_id=observable.id,active=True)
                                status = status2x.status
                                new_status,created = updateStatus(status,
                                                                  existing_tags = existing_tags,
                                                                  added_tags = added_tags)

                                print "STATUS %s %s %s" % (status.id, new_status.id, created)

                            except ObjectDoesNotExist:
                                status = createStatus(added_tags=added_tags)
                                status2x = Status2X(action=action,status=status,active=True,timestamp=timezone.now(),marked=observable)
                                status2x.save()
                                created = False

                            if created or (new_status and new_status.id != status.id):
                                print "Updating status"

                                status2x.active = False
                                status2x.save()
                                print status2x
                                status2x_new = Status2X(action=action,status=new_status,active=True,timestamp=timezone.now(),marked=observable)
                                status2x_new.save()
                                print status2x_new
                                print Status2X.objects.get(content_type=CONTENT_TYPE_SINGLETON_OBSERVABLE,object_id=observable.id,active=True)

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




