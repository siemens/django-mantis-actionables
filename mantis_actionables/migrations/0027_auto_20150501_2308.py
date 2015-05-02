# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('mantis_actionables', '0026_auto_20150312_1341'),
    ]

    operations = [
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
        migrations.AddField(
            model_name='actionabletag',
            name='name',
            field=models.CharField(default='default-name', unique=True, max_length=100, verbose_name='Name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='slug',
            field=models.SlugField(default='default-slug', unique=True, max_length=100, verbose_name='Slug'),
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
        migrations.AlterField(
            model_name='context',
            name='related_incident_id',
            field=models.SlugField(help_text=b'Enter here the number of the associated CERT incident', max_length=40, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='context',
            name='type',
            field=models.SmallIntegerField(default=10, choices=[(10, b'INVES'), (20, b'IR'), (30, b'CERT')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='actionabletag',
            unique_together=set([('context', 'name')]),
        ),
        migrations.RemoveField(
            model_name='actionabletag',
            name='tag',
        ),
        migrations.DeleteModel(
            name='TagName',
        ),
    ]
