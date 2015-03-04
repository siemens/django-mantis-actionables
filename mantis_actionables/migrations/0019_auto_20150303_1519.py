# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mantis_actionables', '0018_auto_20150303_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='stix_entity',
            name='non_iobject_identifier',
            field=models.CharField(max_length=256, blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='stix_entity',
            unique_together=set([('iobject_identifier', 'non_iobject_identifier')]),
        ),
    ]
