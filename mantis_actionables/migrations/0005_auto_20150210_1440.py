# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0004_singletonobservable_mantis_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='SingletonObservableSubtype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='singletonobservable',
            name='subtype',
            field=models.ForeignKey(to='mantis_actionables.SingletonObservableSubtype', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='singletonobservable',
            unique_together=set([('type', 'subtype', 'value')]),
        ),
    ]
