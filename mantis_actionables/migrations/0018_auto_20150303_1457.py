# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0005_AddTaggingHistory'),
        ('mantis_actionables', '0017_auto_20150303_1401'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntityType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='STIX_Entity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('essence', models.TextField(blank=True)),
                ('entity_type', models.ForeignKey(to='mantis_actionables.EntityType')),
                ('iobject_identifier', models.ForeignKey(to='dingos.Identifier', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='source',
            name='iobject',
        ),
        migrations.RemoveField(
            model_name='source',
            name='top_level_iobject',
        ),
        migrations.AddField(
            model_name='source',
            name='related_stix_entities',
            field=models.ManyToManyField(to='mantis_actionables.STIX_Entity'),
            preserve_default=True,
        ),
    ]
