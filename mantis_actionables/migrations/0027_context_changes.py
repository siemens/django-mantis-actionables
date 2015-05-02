# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0026_auto_20150312_1341')
    ]

    operations = [
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
                )
        ]