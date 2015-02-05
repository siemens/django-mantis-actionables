# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import mantis_actionables.models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0005_AddTaggingHistory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField(blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IDSSignature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ImportInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField(blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SignatureType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SingletonObservable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=2048)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SingletonObservableType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=datetime.datetime(2015, 2, 5, 11, 18, 49, 553103))),
                ('origin', models.SmallIntegerField(help_text=b"Chose 'internal (automated input)' for information stemming from automated mechanism such as sandbox reports etc.", choices=[(0, b'Uncertain'), (1, b'Public'), (2, b'Provided by vendor'), (3, b'Provided by partner'), (4, b'Internal (automated input)'), (5, b'Internal (manually selected)')])),
                ('tlp', models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (10, b'White'), (20, b'Green'), (30, b'Amber'), (40, b'Red')])),
                ('url', models.URLField(blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('import_info', models.ForeignKey(related_name=b'actionable_thru', to='mantis_actionables.ImportInfo', null=True)),
                ('iobject', models.ForeignKey(related_name=b'actionable_thru', to='dingos.InfoObject', null=True)),
                ('iobject_fact', models.ForeignKey(related_name=b'actionable_thru', to='dingos.Fact', null=True)),
                ('iobject_factvalue', models.ForeignKey(related_name=b'actionable_thru', to='dingos.FactValue', null=True)),
                ('top_level_iobject', models.ForeignKey(related_name=b'related_actionable_thru', to='dingos.InfoObject')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('false_positive', models.NullBooleanField(help_text=b'If true, the associated information (usually a singleton observable) is regarded as false positiveand never used for detection, no matter what the other status fields say')),
                ('active', models.BooleanField(default=True, help_text=b'If true, the associated information is to be used for detection')),
                ('active_from', models.DateTimeField(default=mantis_actionables.models.get_null_time)),
                ('active_to', models.DateTimeField(default=mantis_actionables.models.get_inf_time)),
                ('tags', models.TextField()),
                ('priority', models.SmallIntegerField(help_text=b'If set to uncertain, it is up to the receiving systemto derive a priority from the additional info providedin the source information.', choices=[(0, b'Uncertain'), (10, b'Low'), (20, b'Medium'), (30, b'High'), (40, b'Hot')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Status2X',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('timestamp', models.DateTimeField()),
                ('object_id', models.PositiveIntegerField()),
                ('action', models.ForeignKey(related_name=b'status_thru', to='mantis_actionables.Action')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('status', models.ForeignKey(related_name=b'actionable_thru', to='mantis_actionables.Status')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('iobject', 'iobject_fact', 'iobject_factvalue', 'top_level_iobject', 'content_type', 'object_id')]),
        ),
        migrations.AddField(
            model_name='singletonobservable',
            name='type',
            field=models.ForeignKey(to='mantis_actionables.SingletonObservableType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='singletonobservable',
            unique_together=set([('type', 'value')]),
        ),
        migrations.AddField(
            model_name='idssignature',
            name='type',
            field=models.ForeignKey(to='mantis_actionables.SignatureType'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='idssignature',
            unique_together=set([('type', 'value')]),
        ),
    ]
