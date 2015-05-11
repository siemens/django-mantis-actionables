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
            unique_together=set([('context', 'info')]),
        ),
        migrations.AlterField(
            model_name='actionabletag',
            name='name',
            field=models.CharField(unique=True, max_length=100, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='actionabletag',
            name='slug',
            field=models.SlugField(unique=True, max_length=100, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='actionabletag',
            name='info',
            field=models.ForeignKey(null=False,to='mantis_actionables.TagInfo')
        )
        ]