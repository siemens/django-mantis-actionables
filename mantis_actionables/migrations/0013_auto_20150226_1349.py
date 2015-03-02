# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0012_auto_20150224_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='top_level_iobject',
            field=models.ForeignKey(related_name='related_actionable_thru', to='dingos.InfoObject', null=True),
            preserve_default=True,
        ),
    ]
