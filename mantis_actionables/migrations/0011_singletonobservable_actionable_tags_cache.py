# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0010_auto_20150217_2021'),
    ]

    operations = [
        migrations.AddField(
            model_name='singletonobservable',
            name='actionable_tags_cache',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
    ]
