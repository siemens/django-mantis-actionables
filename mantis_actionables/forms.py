__author__ = 'Philipp Lang'

import autocomplete_light
from .models import TagName

class TagForm(autocomplete_light.ModelForm):
    tag = autocomplete_light.ChoiceField(widget = autocomplete_light.TextWidget('TagNameAutocompleteActionables'))
    class Meta:
        model = TagName
