# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers
from mantis_actionables.models import TaggedActionableItem,ActionableTag,ActionableTaggingHistory

tags_infos_to_transfer = None

def extract_tag_infos_forward(apps, schema_editor):
    global tags_infos_to_transfer
    ActionableTag2X = apps.get_model("mantis_actionables","ActionableTag2X")
    tags_infos_to_transfer = list(ActionableTag2X.objects.values('actionable_tag__tag__name','actionable_tag__context_id','content_type_id','object_id','actionable_tag_id'))


def save_tags_forward(apps, schema_editor):
    global tags_infos_to_transfer
    tag_id_mapping = {}
    for tag_info in tags_infos_to_transfer:
        atag, created = ActionableTag.objects.get_or_create(context_id=tag_info['actionable_tag__context_id'],
                                                            name=tag_info['actionable_tag__tag__name'])
        tagged_actionable_item = TaggedActionableItem.objects.get_or_create(tag=atag,
                                                                            content_type_id=tag_info['content_type_id'],
                                                                            object_id=tag_info['object_id'])
        tag_id_mapping[tag_info['actionable_tag_id']] = atag.id

    #Update tag info in TaggingHistory
    for entry in ActionableTaggingHistory.objects.all():
        entry.tag_id = tag_id_mapping[entry.tag_id]
        entry.save(update_fields=['tag_id'])

    #delete old actionable tags
    ActionableTag.objects.filter(name="to-delete").delete()


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0001_initial'),
        ('mantis_actionables', '0027_context_changes'),
    ]

    operations = [
        migrations.RunPython(
            extract_tag_infos_forward,
            lambda x,y : None
        ),
        migrations.CreateModel(
            name='TaggedActionableItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField(verbose_name='Object id', db_index=True)),
                ('content_type', models.ForeignKey(related_name='mantis_actionables_taggedactionableitem_tagged_items', verbose_name='Content type', to='contenttypes.ContentType')),
                ('tag', models.ForeignKey(related_name='mantis_actionables_taggedactionableitem_items', to='mantis_actionables.ActionableTag')),
            ],
            options={
                'verbose_name': 'TaggedActionableItem',
                'verbose_name_plural': 'TaggedActionableItems',
            },
            bases=(models.Model,),
        ),
        #migrations.AlterUniqueTogether(
        #    name='actionabletag2x',
        #    unique_together=None,
        #),
        migrations.RemoveField(
            model_name='actionabletag2x',
            name='actionable_tag',
        ),
        migrations.RemoveField(
            model_name='actionabletag2x',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ActionableTag2X',
        ),
        migrations.AlterModelOptions(
            name='actionabletag',
            options={'verbose_name': 'ActionableTag', 'verbose_name_plural': 'ActionableTags'},
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='name',
            field=models.CharField(default='to-delete', unique=False, max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='slug',
            field=models.SlugField(default='to-delete', unique=False, max_length=100, verbose_name='Slug'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='importinfo',
            name='actionable_tags',
            field=taggit.managers.TaggableManager(to='mantis_actionables.ActionableTag', through='mantis_actionables.TaggedActionableItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='singletonobservable',
            name='actionables_tags',
            field=taggit.managers.TaggableManager(to='mantis_actionables.ActionableTag', through='mantis_actionables.TaggedActionableItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),

        migrations.RemoveField(
            model_name='actionabletag',
            name='tag',
        ),
        migrations.DeleteModel(
            name='TagName',
        ),
        migrations.RunPython(
            save_tags_forward,
            lambda x,y : None
        )
    ]
