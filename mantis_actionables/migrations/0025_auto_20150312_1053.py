# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0024_auto_20150311_1335'),
    ]

    operations = [
        migrations.AddField(
            model_name='context',
            name='related_incident_id',
            field=models.SlugField(max_length=40, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='context',
            name='type',
            field=models.SmallIntegerField(default=10, choices=[(10, b'Investigation'), (20, b'Incident')]),
            preserve_default=True,
        ),
    ]
