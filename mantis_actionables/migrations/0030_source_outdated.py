# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0029_make_tags_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='outdated',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
