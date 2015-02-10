__author__ = 'Philipp Lang'

from django import template

from mantis_actionables.forms import TagForm

register = template.Library()

@register.simple_tag()
def show_addTagInput_actionables(obj_id,curr_context):
    form = TagForm()
    form.fields['tag'].widget.attrs.update({
        'data-obj-id': obj_id
        })
    return form.fields['tag'].widget.render('tag','')
