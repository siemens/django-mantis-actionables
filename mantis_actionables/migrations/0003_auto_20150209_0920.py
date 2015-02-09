# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('mantis_actionables', '0002_auto_20150206_1218'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionableTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionableTag2X',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('actionable_tag', models.ForeignKey(related_name=b'actionable_tag_thru', to='mantis_actionables.ActionableTag')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionableTaggingHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('action', models.SmallIntegerField(choices=[(0, b'Added'), (1, b'Removed')])),
                ('comment', models.TextField(blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('tag', models.ForeignKey(related_name=b'actionable_tag_history', to='mantis_actionables.ActionableTag')),
                ('user', models.ForeignKey(related_name=b'actionable_tagging_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Context',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TagName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='context',
            field=models.ForeignKey(to='mantis_actionables.Context', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actionabletag',
            name='tag',
            field=models.ForeignKey(to='mantis_actionables.TagName'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='status2x',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
