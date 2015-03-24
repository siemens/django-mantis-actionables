__author__ = 'Philipp Lang'

from django import template

from dingos import DINGOS_TEMPLATE_FAMILY

from mantis_actionables.forms import TagForm

from mantis_actionables.models import Status

register = template.Library()


@register.filter
def lookup_status_processing(value):
    return Status.PROCESSING_MAP.get(value,'ERROR')

@register.filter
def lookup_status_tlp(value):
    return Status.TLP_MAP.get(value,'ERROR')

@register.filter
def lookup_status_confidence(value):
    return Status.CONFIDENCE_MAP.get(value,'ERROR')





@register.simple_tag()
def show_addTagInput_actionables(obj_id,curr_context):
    form = TagForm()
    form.fields['tag'].widget.attrs.update({
        'data-obj-id': obj_id,
        'data-curr-context': curr_context,
        })
    return form.fields['tag'].widget.render('tag','')

@register.inclusion_tag('mantis_actionables/%s/includes/_ContextMetaDataWidget.html' % DINGOS_TEMPLATE_FAMILY)
def show_ContextMetaData(context_obj,widget_config=None):
    if not widget_config:
        widget_config = {'action_buttons' : ['edit','show_history']}


    context = {'context_obj': context_obj,
               'edit_button' : False,
               'show_history_button': False,
               'show_details_button' : False}

    for button in widget_config.get('action_buttons',[]):
        context["%s_button" % button] = True

    return context

