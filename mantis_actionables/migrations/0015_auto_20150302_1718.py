# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0014_auto_20150302_1401'),
    ]

    operations = [
        migrations.AlterField(
            model_name='importinfo',
            name='create_timestamp',
            field=models.DateTimeField(blank=True),
            preserve_default=True,
        ),
    ]
