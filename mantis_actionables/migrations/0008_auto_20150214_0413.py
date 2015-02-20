# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0007_auto_20150213_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='context',
            name='name',
            field=models.CharField(unique=True, max_length=40),
        ),
        migrations.AlterField(
            model_name='singletonobservablesubtype',
            name='name',
            field=models.CharField(unique=True, max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='singletonobservabletype',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='tagname',
            name='name',
            field=models.CharField(unique=True, max_length=40),
        ),
        migrations.AlterUniqueTogether(
            name='actionabletag2x',
            unique_together=set([('actionable_tag', 'content_type', 'object_id')]),
        ),
    ]
