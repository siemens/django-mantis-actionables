# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dingos', '0005_AddTaggingHistory'),
        ('mantis_actionables', '0019_auto_20150303_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='iobject',
            field=models.ForeignKey(related_name='actionable_thru', to='dingos.InfoObject', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='source',
            name='top_level_iobject',
            field=models.ForeignKey(related_name='related_actionable_thru', to='dingos.InfoObject', null=True),
            preserve_default=True,
        ),
    ]
