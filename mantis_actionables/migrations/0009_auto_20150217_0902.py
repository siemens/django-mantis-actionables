# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0008_auto_20150214_0413'),
    ]

    operations = [
        migrations.AddField(
            model_name='context',
            name='description',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='context',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 17, 9, 1, 59, 973595), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='context',
            name='title',
            field=models.CharField(default=b'', max_length=256, blank=True),
            preserve_default=True,
        ),
    ]
