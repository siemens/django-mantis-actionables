# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0013_auto_20150226_1349'),
    ]

    operations = [
        migrations.AddField(
            model_name='importinfo',
            name='type',
            field=models.SmallIntegerField(default=0, choices=[(0, b'Unknown'), (10, b'Crowdstrike Actor'), (20, b'Crowdstrike Report')]),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='importinfo',
            unique_together=set([('uid', 'namespace')]),
        ),
    ]
