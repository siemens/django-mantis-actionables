__author__ = 'Philipp Lang'

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

import autocomplete_light
from .models import TagName, Context, ActionableTag
from django import forms

from django.forms import widgets

from django.core.validators import RegexValidator

from taggit.models import Tag

from dingos import DINGOS_TAGGING_REGEX

class TagForm(autocomplete_light.ModelForm):
    tag = autocomplete_light.ChoiceField(widget = autocomplete_light.TextWidget('TagNameAutocompleteActionables'))
    class Meta:
        model = TagName

class ContextEditForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.current_type = kwargs.pop('current_type')
        self.current_name = kwargs.pop('current_name')
        super(ContextEditForm,self).__init__(*args,**kwargs)
    title = forms.CharField(
                            max_length=256,
                            widget=widgets.TextInput(attrs={'size':'100','class':'vTextField'}))
    description = forms.CharField(max_length=4096,widget=widgets.Textarea(attrs={'class':'vTextField'}))
    type = forms.ChoiceField(choices=Context.TYPE_CHOICES)
    related_incident_id = forms.SlugField(max_length=40,required=False)

    def clean(self):
        cleaned_data = super(ContextEditForm, self).clean()
        type = int(cleaned_data.get("type"))
        related_incident_id = cleaned_data.get("related_incident_id")

        cleaned_data['new_context_name'] = ''

        if type != self.current_type:
            if not self.current_name.startswith(Context.TYPE_MAP[self.current_type]):
                raise forms.ValidationError("Cannot change type because context name '%s' "
                                            "does not signify current context type '%s'" %(self.current_name,
                Context.TYPE_MAP[self.current_type]))
            else:
                new_context_name = "%s%s" % (Context.TYPE_MAP[type],
                                             self.current_name.split(Context.TYPE_MAP[int(self.current_type)])[1])
                existing_contexts = Context.objects.filter(name=new_context_name)

                if existing_contexts:
                    raise forms.ValidationError("Cannot change type and rename, because there already exists a context %s" % new_context_name)

                existing_actionable_tags = ActionableTag.objects.filter(context__name=new_context_name)

                if existing_actionable_tags:
                    raise forms.ValidationError("Cannot change type and rename, because there already exist actionable tags with context %s" % new_context_name)

                existing_dingos_tags = Tag.objects.filter(name=new_context_name)
                if existing_dingos_tags:
                    raise forms.ValidationError("Cannot change type and rename, because there already exists a MANTIS tag '%s'" % new_context_name)

                if type == Context.TYPE_INCIDENT and not related_incident_id:
                    raise forms.ValidationError("Please provide an incident number when changing type from investigation to incident.")

                cleaned_data['new_context_name'] = new_context_name
        return cleaned_data


