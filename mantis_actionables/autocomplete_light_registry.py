import autocomplete_light
from .models import TagName

class AutocompleteActionables(autocomplete_light.AutocompleteModelBase):
    model = TagName
    search_fields = ['name']
    choices = TagName.objects.all()

    attrs={
        'placeholder': 'Type in tag here..',
        'data-autocomplete-minimum-characters' : 2,
        'id' : "id_tag",
        'data-tag-type' : 'actionables'
        }

autocomplete_light.register(AutocompleteActionables)