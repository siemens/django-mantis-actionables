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

import json
import importlib

from mantis_actionables import MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH, \
                               MANTIS_ACTIONABLES_SRC_META_DATA_FUNCTION_PATH


from mantis_actionables.models import Status, Source




def updateStatus(status,*args,**kwargs):
    source_obj = None

    if MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH:
        mod_name, func_name = MANTIS_ACTIONABLES_STATUS_UPDATE_FUNCTION_PATH.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        update_status_function = getattr(mod,func_name)
        return update_status_function(status,*args,**kwargs)
    else:


        if 'source_obj' in kwargs:
            source_obj = kwargs['source_obj']
        else:
            source_obj = None

        if 'related_entities' in kwargs:
            related_entities = kwargs['related_entities']

        elif  source_obj:
            related_entities = source_obj.related_stix_entities.all()
        else:
            related_entities = []


        if status:
            most_permissive_tlp = status.most_permissive_tlp
            kill_chain_phases = set(status.kill_chain_phases.split(';'))
            max_confidence = status.max_confidence
            active = status.active
            priority = status.priority
            false_positive = status.false_positive
            best_processing = status.best_processing
        else:
            most_permissive_tlp = Status.TLP_UNKOWN
            kill_chain_phases = set([])
            max_confidence = Status.CONFIDENCE_UNKOWN
            active=True
            priority = Status.PRIORITY_UNCERTAIN
            false_positive = False
            best_processing = Status.PROCESSING_UNKNOWN

        if source_obj:
            most_permissive_tlp = max(source_obj.tlp,most_permissive_tlp)
            best_processing = max(source_obj.processing, best_processing)


        for related_entity in related_entities:
            if related_entity.entity_type.name == 'Indicator':
                essence = related_entity.read_essence()
                if 'kill_chain_phases' in essence:

                    kill_chain_phases_list = essence['kill_chain_phases'].split(';')
                    print "KPL"
                    print essence['kill_chain_phases']
                    print kill_chain_phases_list
                    kill_chain_phases.update(kill_chain_phases_list)



                if 'confidence' in essence:
                    max_confidence = max(max_confidence,Status.CONFIDENCE_RMAP[essence['confidence'].lower()])



        kill_chain_phases = ';'.join(kill_chain_phases)




        new_status, created = Status.objects.get_or_create(most_permissive_tlp = most_permissive_tlp,
                                                           kill_chain_phases = kill_chain_phases,
                                                           max_confidence = max_confidence,
                                                           active=active,
                                                           priority = priority,
                                                           false_positive=false_positive,
                                                           best_processing=best_processing)
        return (new_status,created)


def createSourceMetaData(*args,**kwargs):
    print "CAlled Source MetaDAt"
    print kwargs
    if MANTIS_ACTIONABLES_SRC_META_DATA_FUNCTION_PATH:
        mod_name, func_name = MANTIS_ACTIONABLES_SRC_META_DATA_FUNCTION_PATH.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        my_function = getattr(mod,func_name)
        return my_function(*args,**kwargs)
    else:
       result = {'origin': Source.ORIGIN_UNKNOWN,
                 'processing': Source.PROCESSING_UNKNOWN}
    return result



