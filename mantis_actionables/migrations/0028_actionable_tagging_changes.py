# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers
from mantis_actionables.models import TaggedActionableItem,ActionableTag,ActionableTaggingHistory

tags_infos_to_transfer = None

def extract_tag_infos_forward(apps, schema_editor):
    global tags_infos_to_transfer

    ActionableTag2X = apps.get_model("mantis_actionables","ActionableTag2X")
    tags_infos_to_transfer = list(ActionableTag2X.objects.values('content_type_id','object_id','actionable_tag_id'))


def save_tags_forward(apps, schema_editor):
    global tags_infos_to_transfer

    for tag_info in tags_infos_to_transfer:
        tagged_actionable_item, created = TaggedActionableItem.objects.get_or_create(tag_id=tag_info['actionable_tag_id'],
                                                                            content_type_id=tag_info['content_type_id'],
                                                                            object_id=tag_info['object_id'])

    #call save for each ActionableTag in order to fill the name and slug field with unique values
    for atag in ActionableTag.objects.all():
        atag.save()


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
        migrations.RenameModel(
            old_name='TagName',
            new_name='TagInfo',
        ),
        migrations.AlterUniqueTogether(
            name='actionabletag2x',
            unique_together=None,
        ),
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
        migrations.RenameField(
            model_name='actionabletag',
            old_name='tag',
            new_name='info',
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='name',
            field=models.CharField(default='fill-in', unique=False, max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='slug',
            field=models.SlugField(default='fill-in', unique=False, max_length=100, verbose_name='Slug'),
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
            name='actionable_tags',
            field=taggit.managers.TaggableManager(to='mantis_actionables.ActionableTag', through='mantis_actionables.TaggedActionableItem', help_text='A comma-separated list of tags.', verbose_name='Tags'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='actionabletag',
            unique_together=set([('context', 'info')]),
        ),
        migrations.RunPython(
            save_tags_forward,
            lambda x,y : None
        ),
    ]

