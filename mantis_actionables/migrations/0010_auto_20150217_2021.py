# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0009_auto_20150217_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='processing',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Processing uncertain'), (10, b'Automatically processed'), (20, b'Manually processed')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='source',
            name='origin',
            field=models.SmallIntegerField(choices=[(0, b'Origin not external'), (10, b'Origin external, but provenance uncertain'), (10, b'Origin public'), (20, b'Provided by vendor'), (30, b'Provided by partner')]),
        ),
        migrations.AlterField(
            model_name='source',
            name='tlp',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (40, b'White'), (30, b'Green'), (20, b'Amber'), (10, b'Red')]),
        ),
    ]
