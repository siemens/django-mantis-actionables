# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='tags',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='source',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
