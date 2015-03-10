# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0020_auto_20150304_0834'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='best_processing',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Processing uncertain'), (10, b'Automatically processed'), (20, b'Manually processed')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='kill_chain_phases',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='max_confidence',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (10, b'Low'), (20, b'Medium'), (30, b'High')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='status',
            name='most_permissive_tlp',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (40, b'White'), (30, b'Green'), (20, b'Amber'), (10, b'Red')]),
            preserve_default=True,
        ),
    ]
