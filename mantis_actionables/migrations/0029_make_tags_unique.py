# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

class Migration(migrations.Migration):
    dependencies = [
        ('mantis_actionables', '0028_actionable_tagging_changes'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='actionabletag',
            unique_together=set([('context', 'name')]),
        ),
        migrations.AlterField(
                    model_name='actionabletag',
                    name='name',
                    field=models.CharField(unique=True, max_length=100),
                ),
                migrations.AlterField(
                    model_name='actionabletag',
                    name='slug',
                    field=models.SlugField(unique=True, max_length=100),
                )
        ]