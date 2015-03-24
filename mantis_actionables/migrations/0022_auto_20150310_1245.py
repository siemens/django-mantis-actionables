# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0021_auto_20150309_1037'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='importinfo',
            name='related_threatactor',
        ),
        migrations.AddField(
            model_name='importinfo',
            name='related_stix_entities',
            field=models.ManyToManyField(to='mantis_actionables.STIX_Entity'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='importinfo',
            name='type',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (10, b'Bulk Import')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='status',
            name='best_processing',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (10, b'Automated'), (20, b'Manual')]),
            preserve_default=True,
        ),
    ]
